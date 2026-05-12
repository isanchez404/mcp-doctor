from __future__ import annotations

import re
from typing import Any

from mcp_doctor.config import MCPConfig, MCPServerConfig
from mcp_doctor.diagnostics import Diagnostic

_WINDOWS_DRIVE_PATH = re.compile(r"^[A-Za-z]:\\")


def validate_config(config: MCPConfig) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for server in config.servers.values():
        diagnostics.extend(_validate_server(server))
    return diagnostics


def _validate_server(server: MCPServerConfig) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    base_path = f"servers.{server.name}"

    if server.command and server.url:
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="MCPD_CONFIG_TRANSPORT_CONFLICT",
                message="Server defines both 'command' and 'url'. Choose stdio or HTTP transport, not both.",
                path=base_path,
                fix_hint="Remove either 'command' for stdio transport or 'url' for HTTP transport.",
            )
        )
    elif not server.command and not server.url:
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="MCPD_CONFIG_TRANSPORT_MISSING",
                message="Server must define either 'command' for stdio transport or 'url' for HTTP transport.",
                path=base_path,
                fix_hint="Add 'command' plus optional 'args' for a local stdio server, or add 'url' for a remote HTTP MCP server.",
            )
        )

    if "args" in server.raw and not isinstance(server.raw["args"], list):
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="MCPD_CONFIG_ARGS_NOT_LIST",
                message="Server 'args' must be a list of command arguments.",
                path=f"{base_path}.args",
                fix_hint="Change args to an array, e.g. \"args\": [\"-y\", \"@modelcontextprotocol/server-filesystem\", \"/tmp\"].",
            )
        )

    if "env" in server.raw and not isinstance(server.raw["env"], dict):
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="MCPD_CONFIG_ENV_NOT_DICT",
                message="Server 'env' must be an object/dictionary of environment variables.",
                path=f"{base_path}.env",
                fix_hint="Change env to an object, e.g. \"env\": {\"GITHUB_PERSONAL_ACCESS_TOKEN\": \"...\"}.",
            )
        )

    if "headers" in server.raw and not isinstance(server.raw["headers"], dict):
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="MCPD_CONFIG_HEADERS_NOT_DICT",
                message="Server 'headers' must be an object/dictionary of HTTP headers.",
                path=f"{base_path}.headers",
                fix_hint="Change headers to an object, e.g. \"headers\": {\"Authorization\": \"Bearer ...\"}.",
            )
        )

    for index, arg in enumerate(_raw_args(server.raw)):
        if isinstance(arg, str) and _WINDOWS_DRIVE_PATH.match(arg):
            diagnostics.append(
                Diagnostic(
                    severity="warning",
                    code="MCPD_CONFIG_WINDOWS_PATH_WARNING",
                    message=(
                        "Windows-style paths can break across MCP clients if escaping or shell translation is wrong. "
                        "Prefer forward slashes when possible, e.g. C:/Users/name/project."
                    ),
                    path=f"{base_path}.args[{index}]",
                    fix_hint="Prefer forward slashes in MCP configs, e.g. C:/Users/name/project.",
                )
            )

    return diagnostics


def _raw_args(raw: dict[str, Any]) -> list[Any]:
    args = raw.get("args", [])
    if isinstance(args, list):
        return args
    return []
