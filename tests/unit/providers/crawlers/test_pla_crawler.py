"""Tests for PLA (Profit/Loss Analysis) crawler."""

import pytest
from src.ExternalService.providers.crawlers.pla_crawler import PlaCrawler


class TestPlaCrawler:
    """Test PLA crawler."""

    def test_report_id(self):
        """Should return 'pl' for profit/loss analysis."""
        crawler = PlaCrawler()
        assert crawler.report_id == "pl"

    def test_report_type_value(self):
        """Should return correct type value."""
        crawler = PlaCrawler()
        assert crawler.report_type_value == "profit-and-loss-analysis-summary"

    def test_build_url(self):
        """Should use t164sb01 with REPORT_ID=pl."""
        crawler = PlaCrawler()
        url = crawler.build_url(2025, 1)
        assert "t164sb01" in url
        assert "REPORT_ID=pl" in url
        assert "SYEAR=114" in url
        assert "SSEASON=1" in url

    def test_download_returns_result_object(self):
        """Should return DownloadResult."""
        result = PlaCrawler().download(2025, 1)
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')
