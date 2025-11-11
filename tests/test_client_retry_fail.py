"""Covers client retry failure path: second attempt also fails, raising SearchError."""

import pytest
from unittest.mock import MagicMock, patch
from openai import BadRequestError

from src.client import WebSearchClient
from src.models import SearchOptions, SearchError


@pytest.mark.unit
@patch("src.client.OpenAI")
def test_client_retry_fails_then_raises(mock_openai_class, test_api_key):
    mock_client_instance = MagicMock()

    class _Resp:
        request = object()
        status_code = 400
        headers = {}

    # First call: BadRequestError mentioning filters; Second call: generic Exception
    mock_client_instance.responses.create.side_effect = [
        BadRequestError("Parameter 'filters' not supported", response=_Resp(), body=None),
        Exception("network down"),
    ]
    mock_openai_class.return_value = mock_client_instance

    client = WebSearchClient(api_key=test_api_key)
    options = SearchOptions(allowed_domains=["example.com"])  # to add filters

    with pytest.raises(SearchError) as exc:
        client.search("query", options)

    assert exc.value.code == "API_ERROR"
    assert "after retry" in str(exc.value).lower()
    assert mock_client_instance.responses.create.call_count == 2
