from pathlib import Path


def test_launch_docs_exist():
    expected = [
        Path("docs/debugging-guide.md"),
        Path("docs/launch.md"),
        Path(".github/ISSUE_TEMPLATE/diagnostic-report.yml"),
    ]

    for path in expected:
        assert path.exists(), f"missing {path}"
        assert path.read_text().strip(), f"empty {path}"


def test_real_world_fixture_examples_exist():
    expected = [
        Path("examples/fixtures/auth-failure-server.py"),
        Path("examples/fixtures/slow-startup-server.py"),
        Path("examples/fixtures/json-rpc-error-server.py"),
        Path("examples/fixtures/noisy-stdout-server.py"),
        Path("examples/fixtures/stderr-warning-server.py"),
        Path("examples/real-world-fixtures.json"),
    ]

    for path in expected:
        assert path.exists(), f"missing {path}"
        assert path.read_text().strip(), f"empty {path}"
