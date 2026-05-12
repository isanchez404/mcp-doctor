import json

from typer.testing import CliRunner

from mcp_doctor.cli import app

runner = CliRunner()


def test_validate_valid_config_exits_zero(tmp_path):
    config_path = tmp_path / "valid.json"
    config_path.write_text(
        json.dumps({"mcpServers": {"time": {"command": "uvx", "args": ["mcp-server-time"]}}})
    )

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 0
    assert "No problems found" in result.output


def test_validate_invalid_config_exits_one_and_prints_codes(tmp_path):
    config_path = tmp_path / "invalid.json"
    config_path.write_text(
        json.dumps({"mcpServers": {"bad": {"command": "npx", "url": "https://example.com/mcp"}}})
    )

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 1
    assert "MCPD_CONFIG_TRANSPORT_CONFLICT" in result.output


def test_validate_missing_file_exits_two_with_friendly_error(tmp_path):
    config_path = tmp_path / "missing.json"

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 2
    assert "does not exist" in result.output
