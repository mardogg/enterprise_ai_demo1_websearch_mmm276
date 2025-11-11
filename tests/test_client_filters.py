"""Tests for filter-removal retry logic in WebSearchClient.search (BadRequestError path)."""

import pytest
from unittest.mock import MagicMock, patch
from openai import BadRequestError

from src.client import WebSearchClient
from src.models import SearchOptions


@pytest.mark.unit
@patch("src.client.OpenAI")
def test_search_filters_retry_removes_filters(mock_openai_class, test_api_key):
    # First call raises BadRequestError referencing filters; second succeeds
    mock_client_instance = MagicMock()

    class _DummyResponse:
        id = "r1"
        model = "gpt-x"
        created = 0
        output = []

    # Side effects: raise then return dummy
    class _Resp:  # minimal object with .request to satisfy BadRequestError constructor
        request = object()

    mock_client_instance.responses.create.side_effect = [
        BadRequestError("Parameter 'filters' not supported", response=_Resp(), body=None),
        _DummyResponse(),
    ]
    mock_openai_class.return_value = mock_client_instance

    client = WebSearchClient(api_key=test_api_key)
    options = SearchOptions(allowed_domains=["example.com"])  # triggers filters addition
    response_dict = client.search("test query", options)
    # Two calls executed
    assert mock_client_instance.responses.create.call_count == 2
    # After removal, response converted to dict
    assert response_dict["id"] == "r1"
    assert response_dict["model"] == "gpt-x"
