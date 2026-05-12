from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigLoadError(Exception):
    """Raised when an MCP config file cannot be loaded."""


@dataclass(frozen=True)
class MCPServerConfig:
    name: str
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MCPConfig:
    servers: dict[str, MCPServerConfig]
    source_path: Path


def load_config(path: str | Path) -> MCPConfig:
    """Load and normalize common MCP client config shapes."""
    source_path = Path(path)
    if not source_path.exists():
        raise ConfigLoadError(f"Config file does not exist: {source_path}")

    raw_config = _load_raw_config(source_path)
    raw_servers = raw_config.get("mcpServers", raw_config.get("mcp_servers"))
    if raw_servers is None:
        raw_servers = {}
    if not isinstance(raw_servers, dict):
        raise ConfigLoadError(
            "Expected MCP servers to be a mapping under 'mcpServers' or 'mcp_servers'"
        )

    servers: dict[str, MCPServerConfig] = {}
    for name, raw_server in raw_servers.items():
        if not isinstance(raw_server, dict):
            raise ConfigLoadError(f"Server '{name}' must be a mapping")
        servers[str(name)] = _normalize_server(str(name), raw_server)

    return MCPConfig(servers=servers, source_path=source_path)


def _load_raw_config(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text()
    except OSError as exc:
        raise ConfigLoadError(f"Could not read config file {path}: {exc}") from exc

    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        elif path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(text)
        else:
            raise ConfigLoadError(
                f"Unsupported config format '{path.suffix}'. Use .json, .yaml, or .yml"
            )
    except ConfigLoadError:
        raise
    except Exception as exc:
        raise ConfigLoadError(f"Could not parse config file {path}: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigLoadError("Config file root must be a mapping/object")
    return data


def _normalize_server(name: str, raw_server: dict[str, Any]) -> MCPServerConfig:
    return MCPServerConfig(
        name=name,
        command=raw_server.get("command"),
        args=list(raw_server.get("args", [])),
        env=dict(raw_server.get("env", {})),
        url=raw_server.get("url"),
        headers=dict(raw_server.get("headers", {})),
        raw=dict(raw_server),
    )
