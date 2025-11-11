"""Covers troubleshooter path that re-raises SearchError from service.search."""

import pytest
from src.troubleshooter import generate_troubleshoot_result
from src.models import SearchOptions, SearchError


class _SvcRaises:
    def search(self, prompt: str, options: SearchOptions):  # noqa: D401
        raise SearchError(code="API_ERROR", message="fail", details={})


@pytest.mark.unit
def test_troubleshooter_reraises_search_error():
    svc = _SvcRaises()
    with pytest.raises(SearchError):
        generate_troubleshoot_result(
            svc,
            "Laptop/PC", "Dell", "XPS", "Boot loop", "details", None, "low"
        )
