"""Tests for diagnostics module to reach full coverage of logic paths."""

import pytest
from typing import Dict
from src import diagnostics as dx


@pytest.mark.unit
def test_collect_unsupported_os(monkeypatch):
    monkeypatch.setattr(dx.platform, "system", lambda: "FreeBSD")
    out = dx.collect()
    assert "unsupported" in out


@pytest.mark.unit
def test_collect_and_redact(monkeypatch):
    # Patch platform.system to windows to exercise WINDOWS_CMDS loop
    monkeypatch.setattr(dx.platform, "system", lambda: "Windows")
    # Patch run_command to return predictable output containing IP
    monkeypatch.setattr(dx, "run_command", lambda cmd: f"Output for {cmd} 10.0.0.5")
    results = dx.collect(redact_ips=True)
    # All command labels should be present and IP redacted
    assert all(label in results for label, _ in dx.WINDOWS_CMDS)
    assert all("<IP>" in v for v in results.values())


@pytest.mark.unit
def test_collect_no_redact(monkeypatch):
    monkeypatch.setattr(dx.platform, "system", lambda: "Windows")
    monkeypatch.setattr(dx, "run_command", lambda cmd: f"IP 192.168.1.10 for {cmd}")
    results = dx.collect(redact_ips=False)
    assert any("192.168.1.10" in v for v in results.values())


@pytest.mark.unit
def test_summarize(monkeypatch):
    # Build synthetic results covering branches
    results: Dict[str, str] = {
        "Network config": "Ethernet IP <IP>",
        "Ping DNS 8.8.8.8": "Reply from <IP>",
        "Disks": "FreePhysicalMemory=123456",  # triggers storage branch
        "Top snapshot": "cpu usage",            # triggers performance branch
    }
    summary = dx.summarize(results)
    assert summary["Network"]
    assert summary["Connectivity"]
    assert summary["Storage"]
    assert summary["Performance"]
