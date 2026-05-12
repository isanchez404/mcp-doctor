from __future__ import annotations

import tomllib
from pathlib import Path


def test_pyproject_has_release_ready_metadata():
    data = tomllib.loads(Path("pyproject.toml").read_text())
    project = data["project"]

    assert project["name"] == "mcp-doctor"
    assert "keywords" in project
    assert {"mcp", "model-context-protocol", "diagnostics"}.issubset(project["keywords"])
    assert project["classifiers"]
    assert project["urls"]["Source"]
    assert project["urls"]["Issues"]
    assert project["scripts"]["mcp-doctor"] == "mcp_doctor.cli:app"


def test_cli_help_mentions_core_commands_and_examples():
    from typer.testing import CliRunner

    from mcp_doctor.cli import app

    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "validate" in result.output
    assert "probe" in result.output
    assert "doctor" in result.output
    assert "examples/fake-mcp.json" in result.output
