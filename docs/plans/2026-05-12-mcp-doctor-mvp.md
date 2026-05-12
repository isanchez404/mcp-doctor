# MCP Doctor MVP Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a local-first CLI that validates MCP server configs, probes stdio MCP servers, and produces human-readable diagnostics for the most common MCP setup failures.

**Architecture:** Start as a Python package with a Typer CLI and small testable modules. Keep the core independent from the CLI: config loading/normalization, validation rules, subprocess probing, diagnostics rendering. Avoid building a full MCP proxy until validation/probing is useful.

**Tech Stack:** Python 3.11+, uv, pytest, typer, rich, pydantic. Optional MCP SDK integration comes after basic config validation and process spawning are tested.

---

## Product wedge

Working name: `mcp-doctor`

One-liner: “The local-first doctor, tracer, and safety proxy for MCP servers.”

Initial commands:

```bash
mcp-doctor validate path/to/config.json
mcp-doctor validate --client claude-desktop
mcp-doctor probe path/to/config.json --server filesystem
mcp-doctor doctor path/to/config.json
```

Initial supported config shape:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "remote": {
      "url": "https://example.com/mcp",
      "headers": {"Authorization": "Bearer ..."}
    }
  }
}
```

Also support Hermes-style:

```yaml
mcp_servers:
  filesystem:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
```

## Milestone 0: Repo foundation

### Task 1: Create packaging and test skeleton

**Objective:** Create a Python package layout with pytest wired up.

**Files:**
- Create: `pyproject.toml`
- Create: `src/mcp_doctor/__init__.py`
- Create: `tests/`

**Verification:**

```bash
uv run pytest -q
```

Expected: tests run successfully once at least one placeholder test exists.

### Task 2: Add README and project positioning

**Objective:** Explain the problem, audience, and MVP commands.

**Files:**
- Create: `README.md`

**Verification:**
Read the README and confirm it answers:
- What is MCP Doctor?
- Who is it for?
- What works today?
- What is coming next?

## Milestone 1: Config loading and validation

### Task 3: RED - tests for normalizing Claude/Hermes config shapes

**Objective:** Define the desired API for loading MCP configs.

**Files:**
- Create: `tests/test_config_loading.py`

**Tests:**
- `load_config` accepts `mcpServers` and returns normalized server entries.
- `load_config` accepts `mcp_servers` and returns normalized server entries.
- Missing config file returns a diagnostic error, not a traceback.

**Run:**

```bash
uv run pytest tests/test_config_loading.py -q
```

Expected: FAIL because `mcp_doctor.config` does not exist yet.

### Task 4: GREEN - implement config loader

**Objective:** Implement the minimal loader needed to pass Task 3.

**Files:**
- Create: `src/mcp_doctor/config.py`

**Implementation notes:**
- Support `.json`, `.yaml`, `.yml`.
- For YAML, use `yaml.safe_load`.
- Return a small dataclass or Pydantic model.
- Do not execute commands in the loader.

**Verification:**

```bash
uv run pytest tests/test_config_loading.py -q
uv run pytest -q
```

Expected: PASS.

### Task 5: RED - tests for validation rules

**Objective:** Define diagnostics for common invalid MCP configs.

**Files:**
- Create: `tests/test_validation.py`

**Tests:**
- A server cannot define both `command` and `url`.
- A server must define either `command` or `url`.
- `args` must be a list when present.
- `env` and `headers` must be dictionaries when present.
- Windows-looking unescaped paths in JSON-style strings produce a warning.

**Run:**

```bash
uv run pytest tests/test_validation.py -q
```

Expected: FAIL because validation does not exist yet.

### Task 6: GREEN - implement validation diagnostics

**Objective:** Produce structured diagnostics with severity, code, message, and path.

**Files:**
- Create: `src/mcp_doctor/diagnostics.py`
- Modify: `src/mcp_doctor/config.py`
- Create: `src/mcp_doctor/validation.py`

**Verification:**

```bash
uv run pytest tests/test_validation.py -q
uv run pytest -q
```

Expected: PASS.

## Milestone 2: CLI

### Task 7: RED - CLI validate command tests

**Objective:** Define CLI behavior for validation.

**Files:**
- Create: `tests/test_cli_validate.py`

**Tests:**
- `mcp-doctor validate valid.json` exits 0 and prints “No problems found”.
- `mcp-doctor validate invalid.json` exits 1 and prints diagnostic codes.
- `mcp-doctor validate missing.json` exits 2 and prints a friendly error.

**Run:**

```bash
uv run pytest tests/test_cli_validate.py -q
```

Expected: FAIL because CLI does not exist.

### Task 8: GREEN - implement CLI validate

**Objective:** Add the first usable command.

**Files:**
- Create: `src/mcp_doctor/cli.py`
- Modify: `pyproject.toml` scripts section.

**Verification:**

```bash
uv run pytest tests/test_cli_validate.py -q
uv run mcp-doctor validate examples/valid-claude.json
```

Expected: PASS and usable CLI output.

## Milestone 3: Process probing

### Task 9: RED - tests for command existence probe

**Objective:** Detect missing executables before users hit opaque MCP errors.

**Files:**
- Create: `tests/test_probe.py`

**Tests:**
- Existing executable returns OK.
- Missing executable returns diagnostic `MCPD_PROCESS_COMMAND_NOT_FOUND`.
- Probe never passes secret env values into diagnostics.

### Task 10: GREEN - implement probe command

**Objective:** Add `mcp-doctor probe` that validates process prerequisites without needing full protocol support.

**Files:**
- Create: `src/mcp_doctor/probe.py`
- Modify: `src/mcp_doctor/cli.py`

**Verification:**

```bash
uv run pytest tests/test_probe.py -q
uv run mcp-doctor probe examples/valid-claude.json --server filesystem
```

Expected: PASS and clear command availability output.

## Milestone 4: MCP handshake smoke test

### Task 11: RED - contract tests around MCP SDK adapter

**Objective:** Isolate MCP SDK usage behind an adapter so tests can fake it.

**Files:**
- Create: `tests/test_mcp_handshake.py`

**Tests:**
- Handshake timeout becomes structured diagnostic.
- Tool list response shows tool count and names.
- Invalid server stdout/stderr is captured safely.

### Task 12: GREEN - implement MCP SDK handshake

**Objective:** Use the Python MCP SDK for stdio servers if installed.

**Files:**
- Create: `src/mcp_doctor/mcp_client.py`
- Modify: `src/mcp_doctor/cli.py`

**Verification:**

```bash
uv run pytest tests/test_mcp_handshake.py -q
uv run mcp-doctor doctor examples/valid-claude.json
```

Expected: PASS. If MCP SDK is missing, CLI tells the user how to install extras.

## Milestone 5: Examples and launch polish

### Task 13: Add examples

**Files:**
- Create: `examples/valid-claude.json`
- Create: `examples/valid-hermes.yaml`
- Create: `examples/invalid-both-command-and-url.json`
- Create: `examples/missing-command.json`

### Task 14: Add GitHub issue templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/mcp_compatibility_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`

### Task 15: Add CI

**Files:**
- Create: `.github/workflows/test.yml`

**Verification:**

```bash
uv run pytest -q
uv run mcp-doctor validate examples/valid-claude.json
```

Expected: PASS locally and in GitHub Actions.

## Non-goals for MVP

- No hosted service.
- No full web UI.
- No long-running proxy in v0.1.
- No attempt to support every MCP client immediately.
- No secret scanning beyond preventing secret leakage in diagnostics.

## Launch checklist

- README has screenshots or terminal examples.
- Examples reproduce 5 common failure modes.
- Works on macOS and Linux locally.
- Windows path warnings included even before full Windows test matrix.
- Create issues labeled `good first issue`, `client-adapter`, `server-compat`, `security`, `proxy`.
- Post to MCP/Hermes/OpenCode communities only after the CLI catches real failures.
