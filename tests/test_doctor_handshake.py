import sys

from mcp_doctor.config import MCPConfig, MCPServerConfig
from mcp_doctor.doctor import doctor_config


def test_doctor_runs_handshake_after_successful_probe(fake_mcp_server_path):
    config = MCPConfig(
        servers={
            "fake": MCPServerConfig(
                name="fake",
                command=sys.executable,
                args=[str(fake_mcp_server_path)],
                raw={"command": sys.executable, "args": [str(fake_mcp_server_path)]},
            )
        },
        source_path=fake_mcp_server_path.parent / "config.json",
    )

    report = doctor_config(config)

    assert report.ok is True
    assert report.passed_servers == 1
    assert report.failed_servers == 0
    assert report.handshake_results["fake"].tool_names == ["echo"]


def test_doctor_reports_handshake_failure(tmp_path):
    crash_path = tmp_path / "crash.py"
    crash_path.write_text("import sys; print('boom', file=sys.stderr); sys.exit(7)")
    config = MCPConfig(
        servers={
            "crashy": MCPServerConfig(
                name="crashy",
                command=sys.executable,
                args=[str(crash_path)],
                raw={"command": sys.executable, "args": [str(crash_path)]},
            )
        },
        source_path=tmp_path / "config.json",
    )

    report = doctor_config(config)

    assert report.ok is False
    assert report.passed_servers == 0
    assert report.failed_servers == 1
    assert [d.code for d in report.diagnostics] == ["MCPD_HANDSHAKE_PROCESS_EXITED"]


def test_doctor_uses_server_connect_timeout(tmp_path):
    slow_path = tmp_path / "slow.py"
    slow_path.write_text("import time; time.sleep(2)")
    config = MCPConfig(
        servers={
            "slow": MCPServerConfig(
                name="slow",
                command=sys.executable,
                args=[str(slow_path)],
                connect_timeout=0.05,
                raw={"command": sys.executable, "args": [str(slow_path)], "connect_timeout": 0.05},
            )
        },
        source_path=tmp_path / "config.json",
    )

    report = doctor_config(config)

    assert report.ok is False
    assert report.failed_servers == 1
    assert [d.code for d in report.diagnostics] == ["MCPD_HANDSHAKE_TIMEOUT"]
