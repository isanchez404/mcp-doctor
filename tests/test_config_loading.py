import json

import pytest
import yaml

from mcp_doctor.config import ConfigLoadError, load_config


def test_loads_claude_style_mcp_servers(tmp_path):
    config_path = tmp_path / "claude.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                    }
                }
            }
        )
    )

    config = load_config(config_path)

    assert list(config.servers) == ["filesystem"]
    assert config.servers["filesystem"].command == "npx"
    assert config.servers["filesystem"].args == [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/tmp",
    ]
    assert config.servers["filesystem"].url is None


def test_loads_hermes_style_mcp_servers(tmp_path):
    config_path = tmp_path / "hermes.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "mcp_servers": {
                    "time": {
                        "command": "uvx",
                        "args": ["mcp-server-time"],
                    }
                }
            }
        )
    )

    config = load_config(config_path)

    assert list(config.servers) == ["time"]
    assert config.servers["time"].command == "uvx"
    assert config.servers["time"].args == ["mcp-server-time"]


def test_load_config_missing_file_raises_friendly_error(tmp_path):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(ConfigLoadError) as exc_info:
        load_config(missing_path)

    assert "does not exist" in str(exc_info.value)
    assert str(missing_path) in str(exc_info.value)


def test_loads_timeout_fields(tmp_path):
    config_path = tmp_path / "timeouts.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "slow": {
                        "command": "python",
                        "timeout": 45,
                        "connect_timeout": 0.25,
                    }
                }
            }
        )
    )

    config = load_config(config_path)

    assert config.servers["slow"].timeout == 45
    assert config.servers["slow"].connect_timeout == 0.25
