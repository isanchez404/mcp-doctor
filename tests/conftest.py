import sys

import pytest

FAKE_MCP_SERVER = r'''
import json
import sys


def read_message():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            raise SystemExit(0)
        if line in (b"\r\n", b"\n"):
            break
        name, value = line.decode().split(":", 1)
        headers[name.lower()] = value.strip()
    body = sys.stdin.buffer.read(int(headers["content-length"]))
    return json.loads(body)


def write_message(payload):
    body = json.dumps(payload).encode()
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
    sys.stdout.buffer.flush()

while True:
    message = read_message()
    method = message.get("method")
    if method == "initialize":
        write_message({
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fake-mcp", "version": "0.1.0"}
            }
        })
    elif method == "notifications/initialized":
        continue
    elif method == "tools/list":
        write_message({
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {"tools": [{"name": "echo", "description": "Echo text", "inputSchema": {"type": "object"}}]}
        })
    else:
        write_message({"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32601, "message": "unknown"}})
'''


@pytest.fixture
def fake_mcp_server_path(tmp_path):
    server_path = tmp_path / "fake_mcp_server.py"
    server_path.write_text(FAKE_MCP_SERVER)
    return server_path


@pytest.fixture
def fake_mcp_server_config(fake_mcp_server_path):
    return {"command": sys.executable, "args": [str(fake_mcp_server_path)]}
