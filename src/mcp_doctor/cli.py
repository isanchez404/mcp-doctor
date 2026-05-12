from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from mcp_doctor.config import ConfigLoadError, load_config
from mcp_doctor.diagnostics import has_errors
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

    for diagnostic in diagnostics:
        style = "red" if diagnostic.severity == "error" else "yellow"
        console.print(
            f"[{style}]{diagnostic.severity.upper()}[/{style}] "
            f"{diagnostic.code} {diagnostic.path}: {diagnostic.message}"
        )

    raise typer.Exit(1 if has_errors(diagnostics) else 0)
