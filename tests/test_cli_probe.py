import json

from typer.testing import CliRunner

from mcp_doctor.cli import app

runner = CliRunner()


def test_probe_existing_command_exits_zero(tmp_path):
    config_path = tmp_path / "valid.json"
    config_path.write_text(json.dumps({"mcpServers": {"python": {"command": "python"}}}))

    result = runner.invoke(app, ["probe", str(config_path), "--server", "python"])

    assert result.exit_code == 0
    assert "Probe passed" in result.output


def test_probe_missing_command_exits_one_with_code(tmp_path):
    config_path = tmp_path / "invalid.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "missing": {"command": "definitely-not-a-real-mcp-command-xyz"}
                }
            }
        )
    )

    result = runner.invoke(app, ["probe", str(config_path), "--server", "missing"])

    assert result.exit_code == 1
    assert "MCPD_PROCESS_COMMAND_NOT_FOUND" in result.output


def test_probe_missing_config_exits_two(tmp_path):
    result = runner.invoke(app, ["probe", str(tmp_path / "missing.json"), "--server", "time"])

    assert result.exit_code == 2
    assert "does not exist" in result.output
