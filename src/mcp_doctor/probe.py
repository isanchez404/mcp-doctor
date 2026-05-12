from __future__ import annotations

import shutil
from dataclasses import dataclass

from mcp_doctor.config import MCPConfig, MCPServerConfig
from mcp_doctor.diagnostics import Diagnostic


@dataclass(frozen=True)
class ProbeResult:
    server_name: str
    ok: bool
    diagnostics: list[Diagnostic]


def probe_server(config: MCPConfig, server_name: str) -> ProbeResult:
    """Probe local prerequisites for one MCP server without executing it."""
    server = config.servers.get(server_name)
    if server is None:
        return ProbeResult(
            server_name=server_name,
            ok=False,
            diagnostics=[
                Diagnostic(
                    severity="error",
                    code="MCPD_PROBE_SERVER_NOT_FOUND",
                    message=f"Server '{server_name}' was not found in config.",
                    path="servers",
                    fix_hint="Run validate or inspect the config to find the exact configured server names.",
                )
            ],
        )

    diagnostics = _probe_server(server)
    return ProbeResult(
        server_name=server_name,
        ok=not any(d.severity == "error" for d in diagnostics),
        diagnostics=diagnostics,
    )


def _probe_server(server: MCPServerConfig) -> list[Diagnostic]:
    if server.url:
        return []

    if not server.command:
        return [
            Diagnostic(
                severity="error",
                code="MCPD_PROBE_COMMAND_MISSING",
                message="Cannot probe stdio server because no command is configured.",
                path=f"servers.{server.name}.command",
                fix_hint="Add a command for stdio transport, or use a url for HTTP transport.",
            )
        ]

    if shutil.which(server.command) is None:
        return [
            Diagnostic(
                severity="error",
                code="MCPD_PROCESS_COMMAND_NOT_FOUND",
                message=(
                    f"Executable '{server.command}' was not found on PATH. Install it or use an absolute command path."
                ),
                path=f"servers.{server.name}.command",
                fix_hint=_missing_command_hint(server.command),
            )
        ]

    return []


def _missing_command_hint(command: str) -> str:
    if command == "npx":
        return "Install Node.js so npx is available, e.g. brew install node on macOS, or use an absolute path to npx."
    if command == "uvx":
        return "Install uv so uvx is available, e.g. curl -LsSf https://astral.sh/uv/install.sh | sh, or use an absolute path to uvx."
    return "Install the executable, add it to PATH, or replace command with an absolute path."
