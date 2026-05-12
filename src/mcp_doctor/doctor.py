from __future__ import annotations

from dataclasses import dataclass, field

from mcp_doctor.config import MCPConfig
from mcp_doctor.diagnostics import Diagnostic, has_errors
from mcp_doctor.mcp_client import HandshakeResult, handshake_stdio_server
from mcp_doctor.probe import probe_server
from mcp_doctor.validation import validate_config


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    total_servers: int
    passed_servers: int
    failed_servers: int
    diagnostics: list[Diagnostic]
    handshake_results: dict[str, HandshakeResult] = field(default_factory=dict)


def doctor_config(config: MCPConfig) -> DoctorReport:
    """Run validation, prerequisite probes, and stdio MCP handshakes."""
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
    handshake_results: dict[str, HandshakeResult] = {}

    for server_name, server in config.servers.items():
        probe_result = probe_server(config, server_name)
        diagnostics.extend(probe_result.diagnostics)
        if not probe_result.ok:
            failed_servers += 1
            continue

        if server.command:
            handshake_result = handshake_stdio_server(server)
            handshake_results[server_name] = handshake_result
            diagnostics.extend(handshake_result.diagnostics)
            if not handshake_result.ok:
                failed_servers += 1

    passed_servers = total_servers - failed_servers
    return DoctorReport(
        ok=not has_errors(diagnostics),
        total_servers=total_servers,
        passed_servers=passed_servers,
        failed_servers=failed_servers,
        diagnostics=diagnostics,
        handshake_results=handshake_results,
    )
