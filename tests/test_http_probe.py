from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from typer.testing import CliRunner

from mcp_doctor.cli import app
from mcp_doctor.config import MCPConfig, MCPServerConfig
from mcp_doctor.probe import probe_server

runner = CliRunner()


class _StatusHandler(BaseHTTPRequestHandler):
    status = 200

    def do_GET(self):  # noqa: N802 - stdlib API
        self.send_response(self.status)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):  # noqa: A002 - stdlib API
        return


def _http_server(status: int):
    class Handler(_StatusHandler):
        pass

    Handler.status = status
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _config(server: MCPServerConfig) -> MCPConfig:
    return MCPConfig(servers={server.name: server}, source_path=Path("test.json"))


def test_http_probe_reports_reachable_server():
    server_process = _http_server(200)
    try:
        url = f"http://127.0.0.1:{server_process.server_address[1]}/mcp"
        config = _config(MCPServerConfig(name="remote", url=url, raw={"url": url}))

        result = probe_server(config, "remote")

        assert result.ok is True
        assert result.diagnostics == []
    finally:
        server_process.shutdown()


def test_http_probe_reports_http_status_with_hint():
    server_process = _http_server(401)
    try:
        url = f"http://127.0.0.1:{server_process.server_address[1]}/mcp"
        config = _config(
            MCPServerConfig(
                name="remote",
                url=url,
                headers={"Authorization": "Bearer sk-test-secret-value"},
                raw={"url": url, "headers": {"Authorization": "Bearer sk-test-secret-value"}},
            )
        )

        result = probe_server(config, "remote")

        assert result.ok is False
        assert result.diagnostics[0].code == "MCPD_HTTP_STATUS_UNAUTHORIZED"
        assert "401" in result.diagnostics[0].message
        rendered = "\n".join(
            f"{diagnostic.message}\n{diagnostic.fix_hint}" for diagnostic in result.diagnostics
        )
        assert "sk-test-secret-value" not in rendered
    finally:
        server_process.shutdown()


def test_http_probe_reports_unreachable_url():
    config = _config(
        MCPServerConfig(
            name="remote",
            url="http://127.0.0.1:9/mcp",
            raw={"url": "http://127.0.0.1:9/mcp"},
            connect_timeout=0.1,
        )
    )

    result = probe_server(config, "remote")

    assert result.ok is False
    assert result.diagnostics[0].code == "MCPD_HTTP_UNREACHABLE"
    assert result.diagnostics[0].fix_hint


def test_probe_cli_can_check_http_server(tmp_path):
    server_process = _http_server(401)
    try:
        url = f"http://127.0.0.1:{server_process.server_address[1]}/mcp"
        config_path = tmp_path / "http.json"
        config_path.write_text(json.dumps({"mcpServers": {"remote": {"url": url}}}))

        result = runner.invoke(app, ["probe", str(config_path), "--server", "remote"])

        assert result.exit_code == 1
        assert "MCPD_HTTP_STATUS_UNAUTHORIZED" in result.output
    finally:
        server_process.shutdown()
