from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from mcp_doctor.config import ConfigLoadError, load_config
from mcp_doctor.diagnostics import Diagnostic, has_errors
from mcp_doctor.doctor import doctor_config
from mcp_doctor.probe import probe_server
from mcp_doctor.validation import validate_config

app = typer.Typer(help="Diagnose MCP server configs and integrations.")
console = Console()
err_console = Console(stderr=True)


@app.callback()
def main() -> None:
    """Diagnose MCP server configs and integrations."""


@app.command()
def validate(config_path: Path) -> None:
    """Validate an MCP config file."""
    try:
        config = load_config(config_path)
    except ConfigLoadError as exc:
        err_console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(2) from exc

    diagnostics = validate_config(config)
    if not diagnostics:
        console.print("[green]No problems found[/green]")
        raise typer.Exit(0)

    _print_diagnostics(diagnostics)
    raise typer.Exit(1 if has_errors(diagnostics) else 0)


@app.command()
def probe(config_path: Path, server: str = typer.Option(..., "--server", "-s")) -> None:
    """Probe local prerequisites for one MCP server without executing it."""
    try:
        config = load_config(config_path)
    except ConfigLoadError as exc:
        err_console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(2) from exc

    validation_diagnostics = validate_config(config)
    if has_errors(validation_diagnostics):
        _print_diagnostics(validation_diagnostics)
        raise typer.Exit(1)

    result = probe_server(config, server)
    if not result.diagnostics:
        console.print(f"[green]Probe passed[/green] for server '{server}'")
        raise typer.Exit(0)

    _print_diagnostics(result.diagnostics)
    raise typer.Exit(1 if has_errors(result.diagnostics) else 0)


@app.command()
def doctor(config_path: Path) -> None:
    """Validate config and probe every configured MCP server."""
    try:
        config = load_config(config_path)
    except ConfigLoadError as exc:
        err_console.print(f"[red]Config error:[/red] {exc}")
        raise typer.Exit(2) from exc

    report = doctor_config(config)
    summary = f"{report.passed_servers} passed, {report.failed_servers} failed, {report.total_servers} total"

    if report.ok:
        console.print(f"[green]Doctor passed[/green]: {summary}")
        _print_handshake_results(report.handshake_results)
        raise typer.Exit(0)

    console.print(f"[red]Doctor found problems[/red]: {summary}")
    _print_handshake_results(report.handshake_results)
    _print_diagnostics(report.diagnostics)
    raise typer.Exit(1)


def _print_handshake_results(handshake_results: dict) -> None:
    for server_name, result in handshake_results.items():
        if result.ok:
            tools = ", ".join(result.tool_names) if result.tool_names else "no tools reported"
            console.print(f"  [green]{server_name}[/green]: {len(result.tool_names)} tool(s): {tools}")


def _print_diagnostics(diagnostics: list[Diagnostic]) -> None:
    for diagnostic in diagnostics:
        style = "red" if diagnostic.severity == "error" else "yellow"
        console.print(
            f"[{style}]{diagnostic.severity.upper()}[/{style}] "
            f"{diagnostic.code} {diagnostic.path}: {diagnostic.message}"
        )
        if diagnostic.fix_hint:
            console.print(f"  [cyan]Fix:[/cyan] {diagnostic.fix_hint}")
