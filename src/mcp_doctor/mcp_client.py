from __future__ import annotations

import json
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Any

from mcp_doctor.config import MCPServerConfig
from mcp_doctor.diagnostics import Diagnostic


@dataclass(frozen=True)
class HandshakeResult:
    server_name: str
    ok: bool
    tool_names: list[str] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)


def handshake_stdio_server(server: MCPServerConfig, timeout_seconds: float = 5) -> HandshakeResult:
    """Start a stdio MCP server, initialize it, and list tools."""
    if not server.command:
        return HandshakeResult(
            server_name=server.name,
            ok=False,
            diagnostics=[
                Diagnostic(
                    severity="error",
                    code="MCPD_HANDSHAKE_COMMAND_MISSING",
                    message="Cannot run MCP handshake because no stdio command is configured.",
                    path=f"servers.{server.name}.command",
                    fix_hint="Add a command for stdio transport, or use a url for HTTP transport.",
                )
            ],
        )

    process = subprocess.Popen(
        [server.command, *server.args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        env=None,
    )
    stderr_buffer: list[bytes] = []
    stderr_thread = threading.Thread(
        target=_drain_stderr, args=(process, stderr_buffer), daemon=True
    )
    stderr_thread.start()

    try:
        initialize = _request(
            process,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-doctor", "version": "0.1.0"},
                },
            },
            timeout_seconds,
        )
        if "error" in initialize:
            return _error_result(server, "MCPD_HANDSHAKE_INITIALIZE_ERROR", initialize["error"])

        _write_message(process, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools = _request(
            process,
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            timeout_seconds,
        )
        if "error" in tools:
            return _error_result(server, "MCPD_HANDSHAKE_TOOLS_LIST_ERROR", tools["error"])

        tool_names = [tool.get("name", "<unnamed>") for tool in tools.get("result", {}).get("tools", [])]
        return HandshakeResult(server_name=server.name, ok=True, tool_names=tool_names)
    except TimeoutError as exc:
        return HandshakeResult(
            server_name=server.name,
            ok=False,
            diagnostics=[
                Diagnostic(
                    severity="error",
                    code="MCPD_HANDSHAKE_TIMEOUT",
                    message=f"Timed out during MCP handshake: {exc}",
                    path=f"servers.{server.name}",
                    fix_hint="Increase startup timeout or run the MCP server command manually to inspect why it does not respond.",
                )
            ],
        )
    except ProcessExitedError:
        stderr = _stderr_text(stderr_buffer)
        return HandshakeResult(
            server_name=server.name,
            ok=False,
            diagnostics=[
                Diagnostic(
                    severity="error",
                    code="MCPD_HANDSHAKE_PROCESS_EXITED",
                    message=f"MCP server exited before completing handshake.{f' stderr: {stderr}' if stderr else ''}",
                    path=f"servers.{server.name}",
                    fix_hint="Run the configured command manually to inspect the startup error, then retry mcp-doctor doctor.",
                )
            ],
        )
    except Exception as exc:
        return HandshakeResult(
            server_name=server.name,
            ok=False,
            diagnostics=[
                Diagnostic(
                    severity="error",
                    code="MCPD_HANDSHAKE_PROTOCOL_ERROR",
                    message=f"MCP handshake failed: {exc}",
                    path=f"servers.{server.name}",
                    fix_hint="Check that the command speaks MCP over stdio and emits Content-Length framed JSON-RPC messages.",
                )
            ],
        )
    finally:
        _terminate_process(process)


def _request(process: subprocess.Popen[bytes], payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    _write_message(process, payload)
    return _read_message(process, timeout)


def _write_message(process: subprocess.Popen[bytes], payload: dict[str, Any]) -> None:
    if process.stdin is None:
        raise ProcessExitedError()
    body = json.dumps(payload, separators=(",", ":")).encode()
    process.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
    process.stdin.flush()


def _read_message(process: subprocess.Popen[bytes], timeout: float) -> dict[str, Any]:
    if process.stdout is None:
        raise ProcessExitedError()
    deadline = threading.Event()
    result: dict[str, Any] = {}
    error: list[BaseException] = []

    def reader() -> None:
        try:
            result.update(_read_message_blocking(process))
        except BaseException as exc:  # noqa: BLE001 - captured across thread boundary
            error.append(exc)
        finally:
            deadline.set()

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    if not deadline.wait(timeout):
        raise TimeoutError("server did not send a response")
    if error:
        raise error[0]
    return result


def _read_message_blocking(process: subprocess.Popen[bytes]) -> dict[str, Any]:
    assert process.stdout is not None
    headers: dict[str, str] = {}
    while True:
        if process.poll() is not None:
            raise ProcessExitedError()
        line = process.stdout.readline()
        if not line:
            raise ProcessExitedError()
        if line in (b"\r\n", b"\n"):
            break
        name, value = line.decode().split(":", 1)
        headers[name.lower()] = value.strip()
    if "content-length" not in headers:
        raise ValueError("missing Content-Length header")
    body = process.stdout.read(int(headers["content-length"]))
    return json.loads(body)


def _drain_stderr(process: subprocess.Popen[bytes], buffer: list[bytes]) -> None:
    if process.stderr is None:
        return
    while True:
        chunk = process.stderr.readline()
        if not chunk:
            return
        buffer.append(chunk)


def _stderr_text(buffer: list[bytes]) -> str:
    return b"".join(buffer)[-2000:].decode(errors="replace").strip()


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)


def _error_result(server: MCPServerConfig, code: str, error: Any) -> HandshakeResult:
    return HandshakeResult(
        server_name=server.name,
        ok=False,
        diagnostics=[
            Diagnostic(
                severity="error",
                code=code,
                message=f"MCP server returned JSON-RPC error: {error}",
                path=f"servers.{server.name}",
                fix_hint="Run the server manually or inspect its MCP implementation for the failing method.",
            )
        ],
    )


class ProcessExitedError(Exception):
    """Raised when an MCP server exits before sending a complete response."""
