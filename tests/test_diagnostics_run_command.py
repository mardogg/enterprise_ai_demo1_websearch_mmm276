"""Exercise diagnostics.run_command stdout/stderr selection path."""

import pytest
from types import SimpleNamespace
from src import diagnostics as dx


@pytest.mark.unit
def test_run_command_uses_stdout(monkeypatch):
    def fake_run(cmd, shell, capture_output, text, timeout):  # noqa: D401
        return SimpleNamespace(stdout=" ok ", stderr="")
    monkeypatch.setattr(dx.subprocess, "run", fake_run)
    out = dx.run_command("anything")
    assert out.strip() == "ok"


@pytest.mark.unit
def test_run_command_uses_stderr_when_stdout_empty(monkeypatch):
    def fake_run(cmd, shell, capture_output, text, timeout):
        return SimpleNamespace(stdout="", stderr=" error ")
    monkeypatch.setattr(dx.subprocess, "run", fake_run)
    out = dx.run_command("bad")
    assert out.strip() == "error"
