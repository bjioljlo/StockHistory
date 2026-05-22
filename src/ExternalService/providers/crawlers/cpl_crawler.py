"""Comprehensive Profit/Loss (CPL) crawler for TWSE MOPS."""

from src.ExternalService.providers.crawlers.base_crawler import (
    BaseFinancialCrawler,
    DownloadResult,
)


class CplCrawler(BaseFinancialCrawler):
    """Crawler for Comprehensive Profit/Loss (綜合損益表 / 損益表).

    TWSE report_id: is
    """

    @property
    def report_id(self) -> str:
        return "is"

    @property
    def report_type_value(self) -> str:
        return "consolidated-profit-and-loss-summary"

    def download(self, year: int, season: int) -> DownloadResult:
        url = self.build_url(year, season)
        self._logger.info("Downloading CPL statement: %s", url)

        html_text = self._request_with_retry(url)
        if html_text is None:
            self._logger.error("Failed to download CPL statement after %d retries", self.max_retries)
            return DownloadResult.failure(url=url)

        try:
            df = self._parse_html_tables(html_text)
            if df is None or df.empty:
                self._logger.warning("No data found in CPL response")
                return DownloadResult.failure(url=url)

            self._logger.info("Downloaded CPL statement: %d rows, %d columns", *df.shape)
            return DownloadResult(df=df, url=url, success=True)
        except Exception as e:
            self._logger.error("Failed to parse CPL HTML response: %s", e)
            return DownloadResult.failure(url=url)
