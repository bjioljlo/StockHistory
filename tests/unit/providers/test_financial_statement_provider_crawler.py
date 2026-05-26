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

    def test_process_pla_dataframe_maps_to_sql_columns(self, provider):
        """PLA data should normalize headers and map to quarterly_reports SQL columns."""
        raw_df = DataFrame({
            '公司代號': ['1101'],
            '公司名稱': ['台泥'],
            '營業收入': ['34956.26'],
            '毛利率/': ['16.86'],
            '營業利益率/': ['6.58'],
            '稅前純益率/': ['5.41'],
            '稅後 純益率/': ['2.20'],
        })

        processed = provider._process_financial_statement_data(
            raw_df,
            datetime(2025, 3, 15),
            1,
            info.FS_type.PLA,
        )

        assert 'report_type' in processed.columns
        assert processed.loc[0, 'report_type'] == 'PLA'
        assert 'revenue' in processed.columns
        assert 'gross_margin' in processed.columns
        assert 'operating_margin' in processed.columns
        assert 'pre_tax_margin' in processed.columns
        assert 'net_margin' in processed.columns
        assert 'statement_type' not in processed.columns
        assert processed.loc[0, 'revenue'] == pytest.approx(34956.26)
        assert processed.loc[0, 'gross_margin'] == pytest.approx(16.86)

    def test_filter_data_by_reference_csv(self, provider, tmp_path):
        reference_dir = tmp_path / "seasonInfo"
        reference_dir.mkdir()
        reference_file = reference_dir / "2025-season4-profit-and-loss-analysis-summary.csv"
        reference_file.write_text(
            "公司名稱,公司代號,營業收入,毛利率(%),營業利益率(%),稅前純益率(%),稅後純益率(%)\n",
            encoding='utf-8'
        )
        provider._file_path = str(tmp_path)

        raw_df = DataFrame({
            '公司代號': ['1101'],
            '公司名稱': ['台泥'],
            '營業收入': ['149804.14'],
            '毛利率/': ['18.40'],
            '營業利益率/': ['6.73'],
            '稅前純益率/': ['-6.29'],
            '稅後 純益率/': ['-7.92'],
            'extra': ['ignore_me'],
        })

        processed = provider._process_financial_statement_data(
            raw_df,
            datetime(2025, 10, 1),
            4,
            info.FS_type.PLA,
        )

        assert 'extra' not in processed.columns
        assert 'revenue' in processed.columns
        assert 'gross_margin' in processed.columns
        assert 'operating_margin' in processed.columns
        assert 'pre_tax_margin' in processed.columns
        assert 'net_margin' in processed.columns
