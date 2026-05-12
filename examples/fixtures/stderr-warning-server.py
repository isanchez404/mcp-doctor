#!/usr/bin/env python3
import json
import sys

print("warning: optional backend unavailable", file=sys.stderr)


def read_message():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if line in (b"\r\n", b"\n"):
            break
        name, value = line.decode().split(":", 1)
        headers[name.lower()] = value.strip()
    return json.loads(sys.stdin.buffer.read(int(headers["content-length"])))


def write_message(payload):
    body = json.dumps(payload).encode()
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
    sys.stdout.buffer.flush()


request = read_message()
write_message({"jsonrpc": "2.0", "id": request["id"], "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "stderr-warning", "version": "1"}}})
read_message()
request = read_message()
write_message({"jsonrpc": "2.0", "id": request["id"], "result": {"tools": [{"name": "warn-ok"}]}})
