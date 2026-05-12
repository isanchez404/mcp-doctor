import json

from typer.testing import CliRunner

from mcp_doctor.cli import app

runner = CliRunner()


def test_doctor_valid_config_exits_zero_with_summary(tmp_path):
    config_path = tmp_path / "valid.json"
    config_path.write_text(json.dumps({"mcpServers": {"python": {"command": "python"}}}))

    result = runner.invoke(app, ["doctor", str(config_path)])

    assert result.exit_code == 0
    assert "Doctor passed" in result.output
    assert "1 passed, 0 failed" in result.output


def test_doctor_probe_failure_exits_one_with_summary_and_code(tmp_path):
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

    result = runner.invoke(app, ["doctor", str(config_path)])

    assert result.exit_code == 1
    assert "Doctor found problems" in result.output
    assert "0 passed, 1 failed" in result.output
    assert "MCPD_PROCESS_COMMAND_NOT_FOUND" in result.output


def test_doctor_missing_config_exits_two(tmp_path):
    result = runner.invoke(app, ["doctor", str(tmp_path / "missing.json")])

    assert result.exit_code == 2
    assert "does not exist" in result.output
