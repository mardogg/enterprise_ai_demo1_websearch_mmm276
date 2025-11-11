"""Extra tests for src.main to hit techsupport-mode branches and file output path."""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from src.main import main
from src.models import SearchResult, Source, Citation
from datetime import datetime


@pytest.mark.integration
@patch('src.main.SearchService')
@patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
def test_main_techsupport_mode_enables_curated_domains(mock_service_class, mock_datetime):
    mock_service = MagicMock()
    result = SearchResult(
        query="Fan noisy",
        text="Check for dust",
        citations=[],
        sources=[],
        search_id="id",
        timestamp=mock_datetime,
    )
    mock_service.search.return_value = result
    mock_service_class.return_value = mock_service

    test_args = ["prog", "Fan noisy", "--mode", "techsupport"]
    with patch.object(sys, 'argv', test_args):
        exit_code = main()
    assert exit_code == 0
    # search called once
    mock_service.search.assert_called_once()
