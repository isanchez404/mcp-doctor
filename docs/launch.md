# Launch notes

MCP Doctor positioning:

> The boring diagnostic layer for MCP servers: validate configs, probe prerequisites, handshake with stdio servers, check HTTP endpoints, and emit safe pasteable diagnostics.

## Launch checklist

- README explains the problem and first commands.
- `mcp-doctor validate`, `probe`, and `doctor` work locally.
- Example fixtures cover real failure modes.
- Diagnostics include stable machine-readable codes.
- Stderr/protocol errors are redacted before users paste output into issues.
- Issue template asks for config shape and diagnostic output without secrets.

## Suggested announcement

MCP setup failures are still too opaque across Claude Desktop, Hermes, OpenCode, Cursor, and custom agents. `mcp-doctor` is a local-first CLI that tells you whether your MCP config is valid, whether the command or URL is reachable, whether a stdio server actually speaks MCP, and what tools it exposes.

Try it:

```bash
uvx mcp-doctor doctor path/to/config.json
```

Or in this repo:

```bash
uv run --extra dev mcp-doctor doctor examples/fake-mcp.json
```

## Near-term roadmap

- HTTP/StreamableHTTP protocol handshake after reachability checks.
- JSON output for CI and issue automation.
- Client-specific config importers/exporters.
- More fixtures for popular community MCP servers.
