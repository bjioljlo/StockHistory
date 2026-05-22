"""Tests for SCF (Statement of Cash Flows) crawler."""

import pytest
from src.ExternalService.providers.crawlers.scf_crawler import ScfCrawler


class TestScfCrawler:
    """Test SCF crawler."""

    def test_report_id(self):
        """Should return 'cf' for cash flow statement."""
        crawler = ScfCrawler()
        assert crawler.report_id == "cf"

    def test_report_type_value(self):
        """Should return correct type value."""
        crawler = ScfCrawler()
        assert crawler.report_type_value == "statement-of-cash-flows"

    def test_build_url(self):
        """Should build correct TWSE URL for SCF."""
        crawler = ScfCrawler()
        url = crawler.build_url(2025, 3)
        assert "REPORT_ID=cf" in url
        assert "SYEAR=114" in url
        assert "SSEASON=3" in url

    def test_download_returns_result_object(self):
        """Should return DownloadResult."""
        result = ScfCrawler().download(2025, 3)
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')
