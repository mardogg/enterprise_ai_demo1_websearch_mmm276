"""Covers logger.info after display_results (line 223)."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys

from src.main import main
from src.models import SearchResult


@pytest.mark.unit
@patch('src.main.SearchService')
@patch.dict('os.environ', {'OPENAI_API_KEY': 't'})
def test_logger_info_after_display(mock_service_class, mock_datetime, capsys):
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

    with patch('src.main.logger') as mock_logger:
        with patch.object(sys, 'argv', ['prog', 'Q']):
            exit_code = main()
        assert exit_code == 0
        # Ensure logger.info called with 'citations found'
        calls = [c.args[0] for c in mock_logger.info.call_args_list if c.args]
        assert any('citations found' in m for m in calls)
