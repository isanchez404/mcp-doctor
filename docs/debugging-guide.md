# Why your MCP server does not work

MCP Doctor is meant to make MCP failures safe and boring to debug. Start with the least invasive command and only execute a server once static checks pass.

## 1. Validate config shape

```bash
mcp-doctor validate path/to/config.json
```

This catches common cross-client issues:

- missing transport (`command` or `url`)
- both `command` and `url` configured
- `args` not being an array
- `env` or `headers` not being objects
- Windows paths that may need forward slashes

## 2. Probe prerequisites

```bash
mcp-doctor probe path/to/config.json --server filesystem
```

For stdio servers, probe checks whether the configured command is available on `PATH` without executing the MCP server.

For HTTP servers, probe checks URL reachability and HTTP status. It gives targeted hints for auth, forbidden, missing path, server error, and network failures.

## 3. Run the full doctor

```bash
mcp-doctor doctor path/to/config.json
```

For stdio servers, doctor starts the process and performs:

1. `initialize`
2. `notifications/initialized`
3. `tools/list`

It reports the discovered tool names when the handshake succeeds.

## Common failures

### Command not found

Install the missing executable (`npx`, `uvx`, Python, Node, etc.) or use an absolute command path.

### Plain text on stdout

MCP stdio servers must reserve stdout for `Content-Length` framed JSON-RPC messages. Send logs to stderr.

### Startup timeout

Increase `connect_timeout` or run the command manually to see why startup is slow.

### HTTP 401/403

Check configured headers and token scopes. Do not paste secret values into issues; header names are enough.

### Secret leakage concerns

MCP Doctor redacts common token/password/API-key patterns in diagnostics and passes only a filtered baseline environment plus explicit server `env` values to stdio subprocesses.
