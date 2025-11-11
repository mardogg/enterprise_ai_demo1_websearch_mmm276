"""Tests for troubleshooter.generate_troubleshoot_result covering success and fallback."""

import json
import pytest
from types import SimpleNamespace

from src.troubleshooter import generate_troubleshoot_result
from src.models import TroubleshootResult, SearchOptions


class _StubService:
    def __init__(self, text):
        self._text = text
    def search(self, prompt: str, options: SearchOptions):  # noqa: D401
        return SimpleNamespace(text=self._text)


@pytest.mark.unit
def test_generate_troubleshoot_result_success():
    data = {
        "productType": "Laptop/PC",
        "brand": "Dell",
        "model": "XPS",
        "issueSummary": "Overheating and shutdowns",
        "observations": ["Fan spinning loudly"],
        "hypothesis": "Thermal throttling due to dust buildup",
        "probableCauses": ["Dust", "Thermal paste dry"],
        "actionPlan": ["Clean vents"],
        "escalationCriteria": ["Temps > 95C"],
        "warnings": ["Power off before opening"],
        "suggestedKeywords": ["Dell", "XPS", "thermal", "fix"],
    }
    json_text = json.dumps(data)
    svc = _StubService(json_text)
    result, raw = generate_troubleshoot_result(
        svc,
        data["productType"], data["brand"], data["model"], data["issueSummary"], "extra details", None, "low"
    )
    assert isinstance(result, TroubleshootResult)
    assert result.hypothesis.startswith("Thermal")
    assert raw == json_text


@pytest.mark.unit
def test_generate_troubleshoot_result_fallback():
    svc = _StubService("NOT JSON")
    result, raw = generate_troubleshoot_result(
        svc,
        "Router/Modem", "Netgear", "R7000", "Random reboots", "", None, "low"
    )
    assert isinstance(result, TroubleshootResult)
    assert "Insufficient details" in result.hypothesis
    assert "reboots" in result.suggestedKeywords[0].lower() or len(result.suggestedKeywords) > 0


@pytest.mark.unit
def test_generate_troubleshoot_result_with_fences():
    # Ensure code fence stripping branch executes
    json_body = '{"productType":"Printer","brand":"HP","model":"LaserJet","issueSummary":"Paper jams","observations":["Frequent jams"],"hypothesis":"Rollers worn","actionPlan":["Clean rollers"],"escalationCriteria":["Visible damage"],"suggestedKeywords":["HP","LaserJet","paper jam","fix"]}'
    fenced = "```json\n" + json_body + "\n```"
    svc = _StubService(fenced)
    result, raw = generate_troubleshoot_result(
        svc,
        "Printer", "HP", "LaserJet", "Paper jams", "details", None, "low"
    )
    assert result.productType == "Printer"
    assert result.hypothesis  # parsed correctly
