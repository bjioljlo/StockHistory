"""Statement of Cash Flows (SCF) crawler for TWSE MOPS."""

from src.ExternalService.providers.crawlers.base_crawler import (
    BaseFinancialCrawler,
    DownloadResult,
)


class ScfCrawler(BaseFinancialCrawler):
    """Crawler for Statement of Cash Flows (現金流量表).

    TWSE report_id: cf
    """

    @property
    def report_id(self) -> str:
        return "cf"

    @property
    def report_type_value(self) -> str:
        return "statement-of-cash-flows"

    def download(self, year: int, season: int) -> DownloadResult:
        url = self.build_url(year, season)
        self._logger.info("Downloading SCF statement: %s", url)

        html_text = self._request_with_retry(url)
        if html_text is None:
            self._logger.error("Failed to download SCF statement after %d retries", self.max_retries)
            return DownloadResult.failure(url=url)

        try:
            df = self._parse_html_tables(html_text)
            if df is None or df.empty:
                self._logger.warning("No data found in SCF response")
                return DownloadResult.failure(url=url)

            self._logger.info("Downloaded SCF statement: %d rows, %d columns", *df.shape)
            return DownloadResult(df=df, url=url, success=True)
        except Exception as e:
            self._logger.error("Failed to parse SCF HTML response: %s", e)
            return DownloadResult.failure(url=url)
