import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mcp_doctor.config import MCPConfig, MCPServerConfig
from mcp_doctor.doctor import doctor_config


def _config(*servers: MCPServerConfig) -> MCPConfig:
    return MCPConfig(servers={server.name: server for server in servers}, source_path=Path("test.json"))


class _OkHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - stdlib API
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A002 - stdlib API
        return


def test_doctor_passes_when_all_servers_are_valid_and_probeable(fake_mcp_server_path):
    http_server = ThreadingHTTPServer(("127.0.0.1", 0), _OkHandler)
    thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{http_server.server_address[1]}/mcp"
    try:
        config = _config(
            MCPServerConfig(
                name="fake",
                command=sys.executable,
                args=[str(fake_mcp_server_path)],
                raw={"command": sys.executable, "args": [str(fake_mcp_server_path)]},
            ),
            MCPServerConfig(name="remote", url=url, raw={"url": url}),
        )

        report = doctor_config(config)

        assert report.ok is True
        assert report.total_servers == 2
        assert report.passed_servers == 2
        assert report.failed_servers == 0
        assert report.diagnostics == []
    finally:
        http_server.shutdown()


def test_doctor_reports_validation_errors_without_probeing_invalid_config():
    config = _config(
        MCPServerConfig(
            name="bad",
            command="definitely-not-a-real-mcp-command-xyz",
            url="https://example.com/mcp",
            raw={"command": "definitely-not-a-real-mcp-command-xyz", "url": "https://example.com/mcp"},
        )
    )

    report = doctor_config(config)

    assert report.ok is False
    assert report.total_servers == 1
    assert report.passed_servers == 0
    assert report.failed_servers == 1
    assert [d.code for d in report.diagnostics] == ["MCPD_CONFIG_TRANSPORT_CONFLICT"]


def test_doctor_reports_probe_errors_for_all_servers(fake_mcp_server_path):
    config = _config(
        MCPServerConfig(
            name="fake",
            command=sys.executable,
            args=[str(fake_mcp_server_path)],
            raw={"command": sys.executable, "args": [str(fake_mcp_server_path)]},
        ),
        MCPServerConfig(
            name="missing",
            command="definitely-not-a-real-mcp-command-xyz",
            raw={"command": "definitely-not-a-real-mcp-command-xyz"},
        ),
    )

    report = doctor_config(config)

    assert report.ok is False
    assert report.total_servers == 2
    assert report.passed_servers == 1
    assert report.failed_servers == 1
    assert [d.code for d in report.diagnostics] == ["MCPD_PROCESS_COMMAND_NOT_FOUND"]
