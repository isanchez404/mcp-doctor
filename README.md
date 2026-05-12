# MCP Doctor

MCP Doctor is a local-first diagnostics toolkit for Model Context Protocol (MCP) servers and agent integrations.

It helps developers answer: “Why is my MCP server not working in Claude Desktop, Hermes, OpenCode, Cursor, or another agent?”

## MVP scope

Today this repo is being bootstrapped. The first usable CLI will focus on:

- validating MCP config files
- normalizing common client config shapes such as `mcpServers` and `mcp_servers`
- producing structured diagnostics for common mistakes
- probing local stdio server prerequisites
- running real stdio MCP handshakes (`initialize` + `tools/list`)
- using configured MCP env vars without leaking the whole shell environment
- redacting credential-like values from diagnostics

## Planned commands

```bash
mcp-doctor validate path/to/config.json
mcp-doctor probe path/to/config.json --server filesystem
mcp-doctor doctor path/to/config.json
```

## Current usage

MCP Doctor supports Claude-style `mcpServers` and Hermes-style `mcp_servers` config files. Stdio server configs may include:

```json
{
  "mcpServers": {
    "example": {
      "command": "npx",
      "args": ["-y", "some-mcp-server"],
      "env": {"EXPLICIT_TOKEN": "..."},
      "timeout": 120,
      "connect_timeout": 10
    }
  }
}
```

For stdio handshakes, MCP Doctor inherits only a safe baseline environment (`PATH`, `HOME`, `USER`, locale/terminal temp vars, and `XDG_*`) plus explicit server `env` values. It does not pass your full shell environment to MCP subprocesses.

Validate a config:

```bash
uv run mcp-doctor validate examples/valid-claude.json
```

Probe whether a stdio server command is available on PATH:

```bash
uv run mcp-doctor probe examples/valid-claude.json --server filesystem
```

Run a full doctor check across all configured servers:

```bash
uv run mcp-doctor doctor examples/valid-claude.json
```

Run a full stdio MCP handshake smoke test with the bundled fake server:

```bash
uv run mcp-doctor doctor examples/fake-mcp.json
```

Expected output includes the discovered tools:

```text
Doctor passed: 1 passed, 0 failed, 1 total
  fake: 1 tool(s): echo
```

Probe intentionally broken config:

```bash
uv run mcp-doctor probe examples/missing-command.json --server missing
uv run mcp-doctor doctor examples/missing-command.json
```

## Why this exists

MCP is becoming the integration substrate for AI agents, but setup failures are still opaque: missing executables, path issues, invalid schemas, auth problems, server timeouts, transport mismatches, bad stdout/stderr behavior, and client-specific config differences.

MCP Doctor aims to become the boring, reliable debugging layer underneath agent tooling. Its diagnostics are designed to be safe to paste into issues: stderr and protocol errors are redacted for common secret patterns such as GitHub tokens, `sk-...` keys, bearer tokens, passwords, and API keys.

Diagnostics include actionable fix hints, for example:

```text
ERROR MCPD_PROCESS_COMMAND_NOT_FOUND servers.missing.command: Executable 'npx' was not found on PATH.
  Fix: Install Node.js so npx is available, e.g. brew install node on macOS, or use an absolute path to npx.
```
