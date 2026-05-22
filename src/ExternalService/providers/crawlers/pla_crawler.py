"""Profit/Loss Analysis (PLA) crawler for TWSE MOPS.

PLA (營益分析彙總表) uses a different TWSE endpoint (t167sb03)
compared to BS/CPL/SCF which use t164sb01.
"""

from src.ExternalService.providers.crawlers.base_crawler import (
    BaseFinancialCrawler,
    DownloadResult,
)


class PlaCrawler(BaseFinancialCrawler):
    """Crawler for Profit/Loss Analysis (營益分析彙總表).

    TWSE uses t167sb03 endpoint (not t164sb01 like other report types).
    No REPORT_ID parameter needed.
    """

    @property
    def report_id(self) -> str:
        # PLA uses a different endpoint without REPORT_ID
        return ""

    @property
    def report_type_value(self) -> str:
        return "profit-and-loss-analysis-summary"

    def build_url(self, year: int, season: int) -> str:
        """Build TWSE URL for PLA using t167sb03 endpoint.

        PLA (營益分析彙總表) is served by a different endpoint
        compared to BS/CPL/SCF which use t164sb01.
        """
        roc_year = year - 1911 if year > 1990 else year
        return (
            f"https://mopsov.twse.com.tw/server-java/t167sb03"
            f"?step=1&CO_ID=&SYEAR={roc_year}&SSEASON={season}"
        )

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
