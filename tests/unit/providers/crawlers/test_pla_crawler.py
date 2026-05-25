"""Tests for PLA (Profit/Loss Analysis) crawler."""

import pytest
from src.ExternalService.providers.crawlers.pla_crawler import PlaCrawler


class TestPlaCrawler:
    """Test PLA crawler."""

    def test_report_id(self):
        """Should return empty string (PLA uses different endpoint)."""
        crawler = PlaCrawler()
        assert crawler.report_id == ""

    def test_report_type_value(self):
        """Should return correct type value."""
        crawler = PlaCrawler()
        assert crawler.report_type_value == "profit-and-loss-analysis-summary"

    def test_build_url_uses_different_endpoint(self):
        """Should use t167sb03 instead of t164sb01."""
        crawler = PlaCrawler()
        url = crawler.build_url(2025, 1)
        # PLA uses a different TWSE endpoint
        assert "t167sb03" in url
        assert "SYEAR=114" in url
        assert "SSEASON=1" in url
        # PLA has no REPORT_ID parameter
        assert "REPORT_ID" not in url

    def test_download_returns_result_object(self):
        """Should return DownloadResult."""
        result = PlaCrawler().download(2025, 1)
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')
