"""Tests for FinancialStatementProvider crawler integration."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from pandas import DataFrame

from src.Common import InfomationType as info
from src.ExternalService.providers.FinancialStatementProvider import (
    FinancialStatementProvider,
)
from src.ExternalService.providers.crawlers.base_crawler import DownloadResult


class TestFinancialStatementProviderCrawler:
    """Test crawler integration in FinancialStatementProvider."""

    @pytest.fixture
    def provider(self):
        """Create provider with mocked dependencies."""
        sql_service = MagicMock()
        mongo_service = MagicMock()
        read_load_system = MagicMock()
        cache_service = MagicMock()
        cache_service.get.return_value = None  # Miss cache
        return FinancialStatementProvider(
            sql_service, mongo_service, read_load_system, cache_service
        )

    @pytest.mark.parametrize("fs_type,expected_crawler_class_name", [
        (info.FS_type.BS, "BsCrawler"),
        (info.FS_type.CPL, "CplCrawler"),
        (info.FS_type.SCF, "ScfCrawler"),
        (info.FS_type.PLA, "PlaCrawler"),
    ])
    def test_crawler_mapping(self, provider, fs_type, expected_crawler_class_name):
        """Should map each FS_type to correct crawler class."""
        crawler = provider._get_crawler(fs_type)
        assert crawler.__class__.__name__ == expected_crawler_class_name

    def test_bs_crawler_download_success(self, provider):
        """Should delegate BS download to BsCrawler."""
        crawler = provider._get_crawler(info.FS_type.BS)
        # Mock the actual HTTP request by patching _request_with_retry
        with patch.object(crawler, '_request_with_retry', return_value="<html><table></table></html>"):
            with patch("pandas.read_html", return_value=[DataFrame(), DataFrame({"col": [1]})]):
                result = crawler.download(2025, 1)
                assert result.success is True

    def test_crawler_fallback_on_file_missing(self, provider):
        """Should try crawler when file and SQL both empty."""
        # Mock all upstream sources as empty
        provider._get_financial_statement_from_sql = MagicMock(return_value=DataFrame())
        provider._get_financial_statement_from_file = MagicMock(return_value=DataFrame())

        # Mock crawler
        mock_df = DataFrame({"公司代號": ["2330"], "公司名稱": ["台積電"]})
        with patch.object(provider, '_financial_statement_download') as mock_download:
            mock_download.return_value = mock_df
            provider._save_financial_statement_to_db = MagicMock()

            result = provider.get_allstock_financial_statement(
                datetime(2025, 3, 15), info.FS_type.BS
            )
            assert not result.empty
            mock_download.assert_called_once()
