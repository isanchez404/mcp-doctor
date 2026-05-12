from mcp_doctor.config import MCPConfig, MCPServerConfig
from mcp_doctor.probe import probe_server
from mcp_doctor.validation import validate_config


def test_transport_conflict_diagnostic_includes_fix_hint(tmp_path):
    config = MCPConfig(
        servers={
            "bad": MCPServerConfig(
                name="bad",
                command="npx",
                url="https://example.com/mcp",
                raw={"command": "npx", "url": "https://example.com/mcp"},
            )
        },
        source_path=tmp_path / "config.json",
    )

    diagnostic = validate_config(config)[0]

    assert diagnostic.fix_hint == "Remove either 'command' for stdio transport or 'url' for HTTP transport."


def test_missing_npx_command_includes_node_install_hint(tmp_path):
    config = MCPConfig(
        servers={
            "missing": MCPServerConfig(
                name="missing",
                command="npx-missing-for-test",
                raw={"command": "npx-missing-for-test"},
            )
        },
        source_path=tmp_path / "config.json",
    )

    diagnostic = probe_server(config, "missing").diagnostics[0]

    assert "Install the executable" in diagnostic.fix_hint
    assert "absolute path" in diagnostic.fix_hint
