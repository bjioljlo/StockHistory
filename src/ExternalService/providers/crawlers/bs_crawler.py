"""Balance Sheet (BS) crawler for TWSE MOPS."""

from src.ExternalService.providers.crawlers.base_crawler import (
    BaseFinancialCrawler,
    DownloadResult,
)


class BsCrawler(BaseFinancialCrawler):
    """Crawler for Balance Sheet (資產負債表).

    TWSE report_id: bps
    """

    @property
    def report_id(self) -> str:
        return "bps"

    @property
    def report_type_value(self) -> str:
        return "balance-sheet"

    def download(self, year: int, season: int) -> DownloadResult:
        url = self.build_url(year, season)
        self._logger.info("Downloading BS statement: %s", url)

        html_text = self._request_with_retry(url)
        if html_text is None:
            self._logger.error("Failed to download BS statement after %d retries", self.max_retries)
            return DownloadResult.failure(url=url)

        try:
            df = self._parse_html_tables(html_text)
            if df is None or df.empty:
                self._logger.warning("No data found in BS response")
                return DownloadResult.failure(url=url)

            self._logger.info("Downloaded BS statement: %d rows, %d columns", *df.shape)
            return DownloadResult(df=df, url=url, success=True)
        except Exception as e:
            self._logger.error("Failed to parse BS HTML response: %s", e)
            return DownloadResult.failure(url=url)
