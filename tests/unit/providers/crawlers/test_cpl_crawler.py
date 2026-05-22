"""Tests for CPL (Comprehensive Profit/Loss) crawler."""

import pytest
from src.ExternalService.providers.crawlers.cpl_crawler import CplCrawler


class TestCplCrawler:
    """Test CPL crawler."""

    def test_report_id(self):
        """Should return 'is' for income statement."""
        crawler = CplCrawler()
        assert crawler.report_id == "is"

    def test_report_type_value(self):
        """Should return correct type value."""
        crawler = CplCrawler()
        assert crawler.report_type_value == "consolidated-profit-and-loss-summary"

    def test_build_url(self):
        """Should build correct TWSE URL for CPL."""
        crawler = CplCrawler()
        url = crawler.build_url(2024, 4)
        assert "REPORT_ID=is" in url
        assert "SYEAR=113" in url
        assert "SSEASON=4" in url

    def test_download_returns_result_object(self):
        """Should return DownloadResult."""
        result = CplCrawler().download(2024, 4)
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')
