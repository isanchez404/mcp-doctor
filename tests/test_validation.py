from mcp_doctor.config import MCPConfig, MCPServerConfig
from mcp_doctor.validation import validate_config


def _config(server: MCPServerConfig) -> MCPConfig:
    return MCPConfig(servers={server.name: server}, source_path="test.json")  # type: ignore[arg-type]


def test_server_cannot_define_command_and_url():
    config = _config(MCPServerConfig(name="bad", command="npx", url="https://example.com/mcp"))

    diagnostics = validate_config(config)

    assert diagnostics[0].severity == "error"
    assert diagnostics[0].code == "MCPD_CONFIG_TRANSPORT_CONFLICT"
    assert diagnostics[0].path == "servers.bad"


def test_server_must_define_command_or_url():
    config = _config(MCPServerConfig(name="bad"))

    diagnostics = validate_config(config)

    assert diagnostics[0].severity == "error"
    assert diagnostics[0].code == "MCPD_CONFIG_TRANSPORT_MISSING"


def test_args_must_be_list_when_present():
    config = _config(
        MCPServerConfig(name="bad", command="npx", raw={"command": "npx", "args": "not-a-list"})
    )

    diagnostics = validate_config(config)

    assert [d.code for d in diagnostics] == ["MCPD_CONFIG_ARGS_NOT_LIST"]
    assert diagnostics[0].path == "servers.bad.args"


def test_env_and_headers_must_be_dicts_when_present():
    config = _config(
        MCPServerConfig(
            name="bad",
            url="https://example.com/mcp",
            raw={"url": "https://example.com/mcp", "env": [], "headers": []},
        )
    )

    diagnostics = validate_config(config)

    assert [d.code for d in diagnostics] == [
        "MCPD_CONFIG_ENV_NOT_DICT",
        "MCPD_CONFIG_HEADERS_NOT_DICT",
    ]


def test_windows_paths_without_escaping_warn_in_args():
    config = _config(
        MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\isaac\\repo"],
            raw={
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\isaac\\repo"],
            },
        )
    )

    diagnostics = validate_config(config)

    assert [d.code for d in diagnostics] == ["MCPD_CONFIG_WINDOWS_PATH_WARNING"]
    assert diagnostics[0].severity == "warning"
