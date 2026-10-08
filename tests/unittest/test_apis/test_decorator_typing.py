from pathlib import Path

import pytest


def test_api_decorators_preserve_signatures(tmp_path):
    mypy_api = pytest.importorskip("mypy.api")
    project_root = Path(__file__).resolve().parents[3]
    sample = Path(__file__).with_name("typing_samples") / "decorator_signatures.py"
    config = tmp_path / "mypy.ini"
    config.write_text(
        "[mypy]\n"
        f"mypy_path = {project_root}\n"
        "follow_imports = silent\n"
        "ignore_missing_imports = True\n"
        "warn_unused_ignores = True\n"
    )

    stdout, stderr, status = mypy_api.run([
        "--config-file", str(config),
        "--cache-dir", str(tmp_path / "mypy-cache"),
        "--no-incremental", str(sample),
    ])
    assert status == 0, stdout + stderr
