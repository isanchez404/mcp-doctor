# MCP Doctor

MCP Doctor is a local-first diagnostics toolkit for Model Context Protocol (MCP) servers and agent integrations.

It helps developers answer: “Why is my MCP server not working in Claude Desktop, Hermes, OpenCode, Cursor, or another agent?”

## MVP scope

Today this repo is being bootstrapped. The first usable CLI will focus on:

- validating MCP config files
- normalizing common client config shapes such as `mcpServers` and `mcp_servers`
- producing structured diagnostics for common mistakes
- probing local stdio server prerequisites

## Planned commands

```bash
mcp-doctor validate path/to/config.json
mcp-doctor probe path/to/config.json --server filesystem
mcp-doctor doctor path/to/config.json
```

## Why this exists

MCP is becoming the integration substrate for AI agents, but setup failures are still opaque: missing executables, path issues, invalid schemas, auth problems, server timeouts, transport mismatches, and client-specific config differences.

MCP Doctor aims to become the boring, reliable debugging layer underneath agent tooling.
