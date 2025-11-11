"""Force troubleshooter fallback with fenced minimal JSON missing required arrays."""

import pytest
from types import SimpleNamespace

from src.troubleshooter import generate_troubleshoot_result
from src.models import SearchOptions, TroubleshootResult


class _S:
    def __init__(self, text):
        self.text = text


class _Service:
    def __init__(self, text):
        self._text = text
    def search(self, prompt: str, options: SearchOptions):
        return _S(self._text)


@pytest.mark.unit
def test_troubleshooter_fallback_minimal_missing_arrays():
    # Minimal fenced JSON lacking arrays to trigger pydantic validation failure
    fenced = """```json
{"productType":"Laptop/PC","brand":"Dell","model":"XPS","issueSummary":"Boot loop"}
```"""
    svc = _Service(fenced)
    result, raw = generate_troubleshoot_result(
        svc,
        "Laptop/PC", "Dell", "XPS", "Boot loop", "details", None, "low"
    )
    assert isinstance(result, TroubleshootResult)
    assert 'Insufficient details' in result.hypothesis
    # Ensure fallback added expected default observation
    assert any('symptoms' in obs.lower() for obs in result.observations)
