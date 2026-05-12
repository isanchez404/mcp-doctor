from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from mcp_doctor.config import MCPConfig, MCPServerConfig
from mcp_doctor.probe import probe_server


def _config(server: MCPServerConfig) -> MCPConfig:
    return MCPConfig(servers={server.name: server}, source_path=Path("test.json"))


class _OkHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - stdlib API
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A002 - stdlib API
        return


def _http_url() -> tuple[str, ThreadingHTTPServer]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _OkHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return f"http://127.0.0.1:{server.server_address[1]}/mcp", server


def test_existing_executable_returns_ok():
    config = _config(MCPServerConfig(name="python", command="python", raw={"command": "python"}))

    result = probe_server(config, "python")

    assert result.server_name == "python"
    assert result.ok is True
    assert result.diagnostics == []


def test_missing_executable_returns_command_not_found_diagnostic():
    config = _config(
        MCPServerConfig(
            name="missing",
            command="definitely-not-a-real-mcp-command-xyz",
            raw={"command": "definitely-not-a-real-mcp-command-xyz"},
        )
    )

    result = probe_server(config, "missing")

    assert result.ok is False
    assert result.diagnostics[0].severity == "error"
    assert result.diagnostics[0].code == "MCPD_PROCESS_COMMAND_NOT_FOUND"
    assert result.diagnostics[0].path == "servers.missing.command"


def test_unknown_server_returns_friendly_diagnostic():
    config = _config(MCPServerConfig(name="time", command="uvx", raw={"command": "uvx"}))

    result = probe_server(config, "filesystem")

    assert result.ok is False
    assert result.diagnostics[0].code == "MCPD_PROBE_SERVER_NOT_FOUND"
    assert "filesystem" in result.diagnostics[0].message


def test_http_server_probe_does_not_require_command():
    url, server_process = _http_url()
    try:
        config = _config(
            MCPServerConfig(
                name="remote",
                url=url,
                raw={"url": url},
            )
        )

        result = probe_server(config, "remote")

        assert result.ok is True
        assert result.diagnostics == []
    finally:
        server_process.shutdown()


def test_probe_never_leaks_secret_env_values_in_diagnostics():
    secret = "sk-test-secret-value"
    config = _config(
        MCPServerConfig(
            name="missing",
            command="definitely-not-a-real-mcp-command-xyz",
            env={"OPENAI_API_KEY": secret},
            raw={"command": "definitely-not-a-real-mcp-command-xyz", "env": {"OPENAI_API_KEY": secret}},
        )
    )

    result = probe_server(config, "missing")

    rendered = "\n".join(d.message for d in result.diagnostics)
    assert secret not in rendered
    assert "OPENAI_API_KEY" not in rendered
