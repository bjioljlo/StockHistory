"""Tests for BS (Balance Sheet) crawler."""

import pytest
from src.ExternalService.providers.crawlers.bs_crawler import BsCrawler


class TestBsCrawler:
    """Test BS crawler."""

    def test_report_id(self):
        """Should return 'bps' for balance sheet."""
        crawler = BsCrawler()
        assert crawler.report_id == "bps"

    def test_report_type_value(self):
        """Should return correct type value."""
        crawler = BsCrawler()
        assert crawler.report_type_value == "balance-sheet"

    def test_build_url(self):
        """Should build correct TWSE URL for BS."""
        crawler = BsCrawler()
        url = crawler.build_url(2025, 1)
        assert "REPORT_ID=bps" in url
        assert "SYEAR=114" in url
        assert "SSEASON=1" in url

    def test_download_without_network(self):
        """Should return failure result without network (test structure)."""
        result = BsCrawler().download(2025, 1)
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')
