"""Covers diagnostics summarize branch when no patterns match (lines 36-39 remain executed via collect, then summarize returns empties)."""

import pytest
from src import diagnostics as dx


@pytest.mark.unit
def test_collect_and_summarize_no_matches(monkeypatch):
    # Force unsupported system so collect returns {'unsupported': ...} and summarize sees no expected keys
    monkeypatch.setattr(dx.platform, "system", lambda: "Plan9")
    res = dx.collect()
    assert "unsupported" in res
    summary = dx.summarize(res)  # Should produce all empty arrays
    assert all(len(v) == 0 for v in summary.values())
