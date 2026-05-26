"""Base class for TWSE financial statement crawlers."""

import time
import logging
from abc import ABC, abstractmethod
from io import StringIO
from typing import Optional, NamedTuple

import pandas as pd
import requests

from src.Common import Tools


class DownloadResult(NamedTuple):
    """Result of a download attempt."""
    df: pd.DataFrame
    url: str
    success: bool

    @classmethod
    def failure(cls, url: str) -> "DownloadResult":
        return cls(df=pd.DataFrame(), url=url, success=False)


class BaseFinancialCrawler(ABC):
    """Base class for TWSE MOPS financial statement crawlers.

    Each subclass handles one report type (BS, CPL, SCF, PLA).
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self.max_retries = 3
        self.retry_delay = 3

    @property
    @abstractmethod
    def report_id(self) -> str:
        """TWSE API report ID (e.g., 'bps', 'is', 'cf')."""
        ...

    @property
    @abstractmethod
    def report_type_value(self) -> str:
        """Report type value string for file naming (e.g., 'balance-sheet')."""
        ...

    def build_url(self, year: int, season: int) -> str:
        """Build TWSE MOPS URL for the given year and season.

        Args:
            year: Western calendar year (e.g., 2025)
            season: Quarter number (1-4)

        Returns:
            Full TWSE MOPS URL string
        """
        roc_year = year - 1911 if year > 1990 else year
        return (
            f"https://mopsov.twse.com.tw/server-java/t164sb01"
            f"?step=1&CO_ID=&SYEAR={roc_year}&SSEASON={season}"
            f"&REPORT_ID={self.report_id}"
        )

    def _decode_response(self, response: requests.Response) -> str:
        """Decode TWSE response using the best available encoding."""
        # Prefer the encoding declared by the server.
        if response.encoding and response.encoding.lower() != 'iso-8859-1':
            try:
                response.encoding = response.encoding
                return response.text
            except (LookupError, UnicodeDecodeError):
                pass

        # Fall back to common TWSE encodings.
        for encoding in ['utf-8', 'big5', 'cp950', 'big5-hkscs']:
            try:
                response.encoding = encoding
                return response.text
            except (LookupError, UnicodeDecodeError):
                continue

        # Last resort: allow requests to guess.
        return response.text

    def _parse_html_tables(self, html_text: str) -> Optional[pd.DataFrame]:
        """Parse HTML tables from TWSE response.

        Args:
            html_text: Raw HTML response text

        Returns:
            DataFrame if tables found, None otherwise
        """
        dfs = pd.read_html(StringIO(html_text))
        if not dfs:
            return None

        # Target table is usually the second table (index 1)
        df = dfs[1] if len(dfs) >= 2 else dfs[0]

        # Handle MultiIndex columns
        if hasattr(df.columns, 'levels') and len(df.columns.levels) > 1:
            df.columns = df.columns.get_level_values(-1)

        return df

    def _request_with_retry(self, url: str, method: str = "get", data: dict | None = None) -> Optional[str]:
        """Send HTTP request with retry logic.

        Args:
            url: Target URL
            method: HTTP method to use ('get' or 'post').
            data: Form data for POST requests.

        Returns:
            Response text if successful, None otherwise
        """
        for attempt in range(self.max_retries):
            try:
                if method.lower() == "post":
                    r = requests.post(url, data=data, headers=Tools.get_random_headers(), timeout=45)
                else:
                    r = requests.get(url, headers=Tools.get_random_headers(), timeout=45)
                r.raise_for_status()
                return self._decode_response(r)
            except requests.exceptions.RequestException as e:
                self._logger.warning(
                    "Download attempt %d/%d failed: %s",
                    attempt + 1, self.max_retries, e
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        return None

    @abstractmethod
    def download(self, year: int, season: int) -> DownloadResult:
        """Download financial statement for the given year and season.

        Args:
            year: Western calendar year
            season: Quarter number (1-4)

        Returns:
            DownloadResult with parsed DataFrame or empty on failure
        """
        ...
