"""Profit/Loss Analysis (PLA) crawler for TWSE MOPS.

PLA (營益分析彙總表) uses a different TWSE endpoint than the other report types.
"""

from io import StringIO
from typing import Optional

import pandas as pd

from src.ExternalService.providers.crawlers.base_crawler import (
    BaseFinancialCrawler,
    DownloadResult,
)


class PlaCrawler(BaseFinancialCrawler):
    """Crawler for Profit/Loss Analysis (營益分析彙總表).

    TWSE uses ajax_t163sb06 endpoint and form POST parameters instead of
    the standard t164sb01 interface used by BS/CPL/SCF.
    """

    @property
    def report_id(self) -> str:
        # PLA uses a different endpoint without REPORT_ID
        return ""

    @property
    def report_type_value(self) -> str:
        return "profit-and-loss-analysis-summary"

    def build_url(self, year: int, season: int) -> str:
        """Build TWSE URL for PLA using the correct POST endpoint.

        PLA (營益分析彙總表) is served by the `ajax_t163sb06` endpoint,
        and the actual query parameters are sent as form data.
        """
        return "https://mopsov.twse.com.tw/mops/web/ajax_t163sb06"

    def _parse_html_tables(self, html_text: str) -> Optional[pd.DataFrame]:
        """Parse PLA HTML tables and promote the first row to the header if needed."""
        dfs = pd.read_html(StringIO(html_text), header=0)
        if not dfs:
            return None

        df = dfs[0]
        if hasattr(df.columns, 'levels') and len(df.columns.levels) > 1:
            df.columns = df.columns.get_level_values(-1)

        # If pandas did not infer the header row, promote the first row when it contains expected Chinese headers.
        if all(isinstance(col, int) for col in df.columns):
            first_row = df.iloc[0].astype(str)
            header_values = [str(v).strip() for v in first_row.tolist()]
            if any('公司' in value for value in header_values):
                df.columns = header_values
                df = df.iloc[1:].reset_index(drop=True)

        return df

    def download(self, year: int, season: int) -> DownloadResult:
        url = self.build_url(year, season)
        self._logger.info("Downloading PLA statement: %s", url)

        roc_year = year - 1911 if year > 1990 else year
        post_data = {
            "encodeURIComponent": 1,
            "step": 1,
            "firstin": 1,
            "off": 1,
            "TYPEK": "sii",
            "year": roc_year,
            "season": season,
        }

        html_text = self._request_with_retry(url, method="post", data=post_data)
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
