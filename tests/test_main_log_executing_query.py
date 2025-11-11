"""Covers the logger.info line 'Executing search query: ...' near line 223 of main.py."""

import pytest
from unittest.mock import patch, MagicMock
from src.main import main
from src.models import SearchResult
import sys


@pytest.mark.unit
@patch('src.main.SearchService')
@patch('src.main.get_logger')
@patch.dict('os.environ', {'OPENAI_API_KEY': 't'})
def test_logs_executing_query(mock_get_logger, mock_service_class, mock_datetime):
    mock_service = MagicMock()
    mock_service.search.return_value = SearchResult(
        query='Q', text='T', citations=[], sources=[], search_id='id', timestamp=mock_datetime
    )
    mock_service_class.return_value = mock_service

    fake_logger = MagicMock()
    mock_get_logger.return_value = fake_logger

    with patch.object(sys, 'argv', ['prog', 'Q']):
        exit_code = main()
    assert exit_code == 0
    # Ensure the specific log message fired
    msgs = [c.args[0] for c in fake_logger.info.call_args_list if c.args]
    assert any("Executing search query:" in m for m in msgs)
