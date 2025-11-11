"""Covers the 'Searching...' verbose print path before executing search."""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from src.main import main
from src.models import SearchResult


@pytest.mark.unit
@patch('src.main.SearchService')
@patch.dict('os.environ', {'OPENAI_API_KEY': 't'})
def test_verbose_searching_print(mock_service_class, mock_datetime):
    mock_service = MagicMock()
    result = SearchResult(
        query="Q",
        text="T",
        citations=[],
        sources=[],
        search_id="id",
        timestamp=mock_datetime
    )
    mock_service.search.return_value = result
    mock_service_class.return_value = mock_service

    cap = StringIO()
    with patch.object(sys, 'argv', ['prog', 'Q', '--verbose']):
        with patch('sys.stdout', cap):
            exit_code = main()
    assert exit_code == 0
    assert 'Searching...' in cap.getvalue()
