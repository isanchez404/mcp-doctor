from __future__ import annotations

from dataclasses import dataclass

from mcp_doctor.config import MCPConfig
from mcp_doctor.diagnostics import Diagnostic, has_errors
from mcp_doctor.probe import probe_server
from mcp_doctor.validation import validate_config


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    total_servers: int
    passed_servers: int
    failed_servers: int
    diagnostics: list[Diagnostic]


def doctor_config(config: MCPConfig) -> DoctorReport:
    """Run validation and prerequisite probes for all configured MCP servers."""
    validation_diagnostics = validate_config(config)
    total_servers = len(config.servers)

    if has_errors(validation_diagnostics):
        return DoctorReport(
            ok=False,
            total_servers=total_servers,
            passed_servers=0,
            failed_servers=total_servers,
            diagnostics=validation_diagnostics,
        )

    diagnostics: list[Diagnostic] = list(validation_diagnostics)
    failed_servers = 0

    for server_name in config.servers:
        result = probe_server(config, server_name)
        diagnostics.extend(result.diagnostics)
        if not result.ok:
            failed_servers += 1

    passed_servers = total_servers - failed_servers
    return DoctorReport(
        ok=not has_errors(diagnostics),
        total_servers=total_servers,
        passed_servers=passed_servers,
        failed_servers=failed_servers,
        diagnostics=diagnostics,
    )
