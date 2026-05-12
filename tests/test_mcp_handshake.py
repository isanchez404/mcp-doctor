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
