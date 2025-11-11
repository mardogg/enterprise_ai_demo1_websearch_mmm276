"""Additional client error-path tests for coverage."""

import pytest
from unittest.mock import MagicMock, patch
from openai import BadRequestError

from src.client import WebSearchClient
from src.models import SearchError


@pytest.mark.unit
@patch("src.client.OpenAI")
def test_search_badrequest_no_filters_maps_to_api_error(mock_openai_class, test_api_key):
    mock_client_instance = MagicMock()

    class _Resp:
        request = object()
        status_code = 400
        headers = {}

    mock_client_instance.responses.create.side_effect = [
        BadRequestError("Some other error", response=_Resp(), body=None),
    ]
    mock_openai_class.return_value = mock_client_instance

    client = WebSearchClient(api_key=test_api_key)
    with pytest.raises(SearchError) as exc:
        client.search("query")
    # Should raise our SearchError wrapper with API_ERROR code in message
    assert exc.value.code == "API_ERROR"
