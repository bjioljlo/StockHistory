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
    """Integration tests (hit actual TWSE website)."""

    @pytest.mark.parametrize("crawler_cls,report_name", [
        (BsCrawler, "BS"),
        (CplCrawler, "CPL"),
        (ScfCrawler, "SCF"),
        (PlaCrawler, "PLA"),
    ])
    def test_download_latest_season(self, crawler_cls, report_name):
        """Should download latest season data from TWSE."""
        crawler = crawler_cls()
        # Try downloading most recent completed season (2025 Q1)
        result = crawler.download(2025, 1)

        # Check result structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')

        if result.success:
            assert not result.df.empty
            assert len(result.df.columns) >= 2  # At least company code + data
        else:
            # TWSE might not have data for future quarters
            pytest.skip(f"{report_name} data not available for 2025 Q1")

    def test_bs_download_has_expected_columns(self):
        """Downloaded BS should contain balance sheet fields."""
        crawler = BsCrawler()
        result = crawler.download(2024, 4)
        if result.success:
            df = result.df
            # Should have columns related to assets/liabilities
            all_text = " ".join(str(col) for col in df.columns)
            assert any(keyword in all_text for keyword in ["資產", "負債", "權益"])

    def test_cpl_download_has_expected_columns(self):
        """Downloaded CPL should contain income statement fields."""
        crawler = CplCrawler()
        result = crawler.download(2024, 4)
        if result.success:
            df = result.df
            all_text = " ".join(str(col) for col in df.columns)
            assert any(keyword in all_text for keyword in ["收入", "利益", "損益"])

    def test_pla_download_uses_correct_endpoint(self):
        """PLA should use t167sb03 endpoint."""
        crawler = PlaCrawler()
        url = crawler.build_url(2024, 1)
        assert "t167sb03" in url
