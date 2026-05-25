"""Integration tests for financial statement crawlers.

These tests connect to the actual TWSE website.
Marked with @pytest.mark.integration to run separately.
"""

import pytest
from src.ExternalService.providers.crawlers.bs_crawler import BsCrawler
from src.ExternalService.providers.crawlers.cpl_crawler import CplCrawler
from src.ExternalService.providers.crawlers.scf_crawler import ScfCrawler
from src.ExternalService.providers.crawlers.pla_crawler import PlaCrawler


@pytest.mark.integration
class TestFinancialStatementCrawlersIntegration:
    """Integration tests (hit actual TWSE website).

    Note: Without a specific CO_ID (stock symbol), TWSE returns a stock
    selection form page, not the full financial data table. Therefore we
    only verify the request/response flow works (URL building, HTTP status,
    and table parsing do not crash). Full data download is handled per-stock
    in FinancialStatementProvider.
    """

    @pytest.mark.parametrize("crawler_cls,report_name", [
        (BsCrawler, "BS"),
        (CplCrawler, "CPL"),
        (ScfCrawler, "SCF"),
        (PlaCrawler, "PLA"),
    ])
    def test_download_request_succeeds(self, crawler_cls, report_name):
        """Should successfully connect to TWSE and return a response."""
        crawler = crawler_cls()
        result = crawler.download(2025, 1)

        assert hasattr(result, 'success'), "Missing 'success' attribute"
        assert hasattr(result, 'df'), "Missing 'df' attribute"
        assert hasattr(result, 'url'), "Missing 'url' attribute"
        assert "mopsov.twse.com.tw" in result.url, "URL should point to TWSE"

    def test_bs_builds_correct_url(self):
        """BS crawler should build t164sb01 URL with REPORT_ID=bps."""
        crawler = BsCrawler()
        url = crawler.build_url(2024, 4)
        assert "t164sb01" in url
        assert "REPORT_ID=bps" in url
        assert "SYEAR=113" in url
        assert "SSEASON=4" in url

    def test_cpl_builds_correct_url(self):
        """CPL crawler should build t164sb01 URL with REPORT_ID=is."""
        crawler = CplCrawler()
        url = crawler.build_url(2024, 4)
        assert "t164sb01" in url
        assert "REPORT_ID=is" in url

    def test_scf_builds_correct_url(self):
        """SCF crawler should build t164sb01 URL with REPORT_ID=cf."""
        crawler = ScfCrawler()
        url = crawler.build_url(2025, 3)
        assert "t164sb01" in url
        assert "REPORT_ID=cf" in url
        assert "SYEAR=114" in url
        assert "SSEASON=3" in url

    def test_pla_builds_correct_url(self):
        """PLA should use t167sb03 endpoint (different from other three)."""
        crawler = PlaCrawler()
        url = crawler.build_url(2024, 1)
        assert "t167sb03" in url
        assert "t164sb01" not in url, "PLA must NOT use t164sb01"
        assert "REPORT_ID" not in url, "PLA has no REPORT_ID parameter"
