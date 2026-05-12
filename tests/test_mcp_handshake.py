import sys
from pathlib import Path

from mcp_doctor.config import MCPConfig, MCPServerConfig
from mcp_doctor.mcp_client import handshake_stdio_server


def test_stdio_handshake_lists_tools(fake_mcp_server_path: Path):
    server = MCPServerConfig(
        name="fake",
        command=sys.executable,
        args=[str(fake_mcp_server_path)],
        raw={"command": sys.executable, "args": [str(fake_mcp_server_path)]},
    )

    result = handshake_stdio_server(server, timeout_seconds=3)

    assert result.ok is True
    assert result.tool_names == ["echo"]
    assert result.diagnostics == []


def test_stdio_handshake_reports_startup_crash(tmp_path):
    crash_path = tmp_path / "crash.py"
    crash_path.write_text("import sys; print('boom', file=sys.stderr); sys.exit(7)")
    server = MCPServerConfig(
        name="crashy",
        command=sys.executable,
        args=[str(crash_path)],
        raw={"command": sys.executable, "args": [str(crash_path)]},
    )

    result = handshake_stdio_server(server, timeout_seconds=3)

    assert result.ok is False
    assert result.diagnostics[0].code == "MCPD_HANDSHAKE_PROCESS_EXITED"
    assert "boom" in result.diagnostics[0].message
    assert result.diagnostics[0].fix_hint


def test_stdio_handshake_passes_configured_env_without_leaking_shell_env(tmp_path, monkeypatch):
    env_server_path = tmp_path / "env_server.py"
    env_server_path.write_text(
        """
import json
import os
import sys

if os.environ.get('MCP_DOCTOR_ALLOWED') != 'yes':
    print('missing configured env', file=sys.stderr)
    sys.exit(3)
if 'MCP_DOCTOR_SHOULD_NOT_LEAK' in os.environ:
    print('leaked shell secret ghp_1234567890abcdef', file=sys.stderr)
    sys.exit(4)


def read_message():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if line in (b'\\r\\n', b'\\n'):
            break
        name, value = line.decode().split(':', 1)
        headers[name.lower()] = value.strip()
    return json.loads(sys.stdin.buffer.read(int(headers['content-length'])))


def write_message(payload):
    body = json.dumps(payload).encode()
    sys.stdout.buffer.write(f'Content-Length: {len(body)}\\r\\n\\r\\n'.encode() + body)
    sys.stdout.buffer.flush()

request = read_message()
write_message({'jsonrpc': '2.0', 'id': request['id'], 'result': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'serverInfo': {'name': 'env', 'version': '1'}}})
read_message()
request = read_message()
write_message({'jsonrpc': '2.0', 'id': request['id'], 'result': {'tools': [{'name': 'env-ok'}]}})
""".strip()
    )
    monkeypatch.setenv("MCP_DOCTOR_SHOULD_NOT_LEAK", "ghp_1234567890abcdef")
    server = MCPServerConfig(
        name="env",
        command=sys.executable,
        args=[str(env_server_path)],
        env={"MCP_DOCTOR_ALLOWED": "yes"},
        raw={"command": sys.executable, "args": [str(env_server_path)], "env": {"MCP_DOCTOR_ALLOWED": "yes"}},
    )

    result = handshake_stdio_server(server, timeout_seconds=3)

    assert result.ok is True
    assert result.tool_names == ["env-ok"]


def test_stdio_handshake_redacts_secrets_from_stderr(tmp_path):
    crash_path = tmp_path / "secret_crash.py"
    crash_path.write_text(
        "import sys; print('token ghp_1234567890abcdef password=swordfish', file=sys.stderr); sys.exit(7)"
    )
    server = MCPServerConfig(
        name="secret",
        command=sys.executable,
        args=[str(crash_path)],
        raw={"command": sys.executable, "args": [str(crash_path)]},
    )

    result = handshake_stdio_server(server, timeout_seconds=3)

    assert result.ok is False
    message = result.diagnostics[0].message
    assert "ghp_1234567890abcdef" not in message
    assert "swordfish" not in message
    assert "[REDACTED]" in message


def test_stdio_handshake_reports_plain_stdout_before_mcp_framing(tmp_path):
    noisy_path = tmp_path / "noisy.py"
    noisy_path.write_text("import sys; print('starting up on stdout'); sys.stdout.flush(); sys.exit(2)")
    server = MCPServerConfig(
        name="noisy",
        command=sys.executable,
        args=[str(noisy_path)],
        raw={"command": sys.executable, "args": [str(noisy_path)]},
    )

    result = handshake_stdio_server(server, timeout_seconds=3)

    assert result.ok is False
    assert result.diagnostics[0].code == "MCPD_HANDSHAKE_STDOUT_NOISE"
    assert "starting up on stdout" in result.diagnostics[0].message
