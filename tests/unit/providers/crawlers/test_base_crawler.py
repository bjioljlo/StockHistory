"""Tests for base crawler class."""

import pytest
from pandas import DataFrame
from src.ExternalService.providers.crawlers.base_crawler import (
    BaseFinancialCrawler,
    DownloadResult,
)


class TestDownloadResult:
    """Test DownloadResult named tuple."""

    def test_download_result_creation(self):
        """Should create DownloadResult with df, url, and success flag."""
        df = DataFrame({"col1": [1, 2]})
        result = DownloadResult(df=df, url="https://example.com", success=True)
        assert result.success is True
        assert result.url == "https://example.com"
        assert not result.df.empty

    def test_download_result_failure(self):
        """Should create DownloadResult with empty df on failure."""
        result = DownloadResult.failure(url="https://example.com")
        assert result.success is False
        assert result.df.empty


class TestBaseFinancialCrawler:
    """Test base crawler abstract class."""

    def test_cannot_instantiate_base_class(self):
        """Should raise TypeError when instantiating abstract class."""
        with pytest.raises(TypeError):
            BaseFinancialCrawler()  # type: ignore

    def test_concrete_subclass_can_instantiate(self):
        """Should allow instantiation of concrete subclass."""

        class ConcreteCrawler(BaseFinancialCrawler):
            @property
            def report_id(self) -> str:
                return "test"

            @property
            def report_type_value(self) -> str:
                return "test-type"

            def download(self, year: int, season: int) -> DownloadResult:
                return DownloadResult.failure(url="http://test.com")

        crawler = ConcreteCrawler()
        assert crawler.report_id == "test"
        assert crawler.report_type_value == "test-type"

    def test_build_url(self):
        """Should build correct TWSE URL."""

        class ConcreteCrawler(BaseFinancialCrawler):
            @property
            def report_id(self) -> str:
                return "bps"

            @property
            def report_type_value(self) -> str:
                return "balance-sheet"

            def download(self, year: int, season: int) -> DownloadResult:
                return DownloadResult.failure(url="http://test.com")

        crawler = ConcreteCrawler()
        # 2025 (民國114年), season 2
        url = crawler.build_url(2025, 2)
        assert "mopsov.twse.com.tw" in url
        assert "SYEAR=114" in url
        assert "SSEASON=2" in url
        assert "REPORT_ID=bps" in url

    def test_default_retry_settings(self):
        """Should have default retry settings."""

        class ConcreteCrawler(BaseFinancialCrawler):
            @property
            def report_id(self) -> str:
                return "bps"

            @property
            def report_type_value(self) -> str:
                return "balance-sheet"

            def download(self, year: int, season: int) -> DownloadResult:
                return DownloadResult.failure(url="http://test.com")

        crawler = ConcreteCrawler()
        assert crawler.max_retries == 3
        assert crawler.retry_delay == 3
