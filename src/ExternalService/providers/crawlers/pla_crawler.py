"""Profit/Loss Analysis (PLA) crawler for TWSE MOPS.

PLA (營益分析彙總表) uses the same t164sb01 endpoint
as BS/CPL/SCF, with REPORT_ID=pl instead of bps/is/cf.
"""

from src.ExternalService.providers.crawlers.base_crawler import (
    BaseFinancialCrawler,
    DownloadResult,
)


class PlaCrawler(BaseFinancialCrawler):
    """Crawler for Profit/Loss Analysis (營益分析彙總表).

    TWSE uses the same t164sb01 endpoint with REPORT_ID=pl.
    """

    @property
    def report_id(self) -> str:
        return "pl"

    @property
    def report_type_value(self) -> str:
        return "profit-and-loss-analysis-summary"

    def download(self, year: int, season: int) -> DownloadResult:
        url = self.build_url(year, season)
        self._logger.info("Downloading PLA statement: %s", url)

        html_text = self._request_with_retry(url)
        if html_text is None:
            self._logger.error("Failed to download PLA statement after %d retries", self.max_retries)
            return DownloadResult.failure(url=url)

        try:
            df = self._parse_html_tables(html_text)
            if df is None or df.empty:
                self._logger.warning("No data found in PLA response")
                return DownloadResult.failure(url=url)

            self._logger.info("Downloaded PLA statement: %d rows, %d columns", *df.shape)
            return DownloadResult(df=df, url=url, success=True)
        except Exception as e:
            self._logger.error("Failed to parse PLA HTML response: %s", e)
            return DownloadResult.failure(url=url)
