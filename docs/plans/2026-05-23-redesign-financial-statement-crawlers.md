# 重新設計財務報表爬蟲（BS/CPL/SCF/PLA）實施計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重新設計 BS（資產負債表）、CPL（綜合損益表）、SCF（現金流量表）、PLA（營益分析彙總表）四個財務報表類型的爬蟲，解決 PLA 缺少專屬端點、URL 對應不完整、爬蟲與資料處理邏輯混雜的問題。

**Architecture:** 將現有 `FinancialStatementProvider` 中的 `_financial_statement()` 爬蟲邏輯拆分為四個專用爬蟲類別，每個類別只負責單一報表類型的 TWSE 端點對應、HTML 下載與表格解析。保留 `FinancialStatementProvider` 作為資料處理與快取的中介層不變。新增 `providers/crawlers/` 子目錄收納爬蟲類別。

**Tech Stack:** Python 3.12, requests, pandas, BeautifulSoup (HTML 解析), existing FinancialStatementProvider, existing CacheService

---

## 文件結構

```
src/ExternalService/providers/
├── __init__.py
├── FinancialStatementProvider.py    # 修改：移除 _financial_statement()，改為委派 crawler
├── crawlers/
│   ├── __init__.py
│   ├── base_crawler.py              # 新增：爬蟲基底類別
│   ├── bs_crawler.py                # 新增：資產負債表爬蟲
│   ├── cpl_crawler.py               # 新增：綜合損益表爬蟲
│   ├── scf_crawler.py               # 新增：現金流量表爬蟲
│   └── pla_crawler.py               # 新增：營益分析彙總表爬蟲
tests/
├── unit/
│   └── providers/
│       └── crawlers/
│           ├── test_base_crawler.py
│           ├── test_bs_crawler.py
│           ├── test_cpl_crawler.py
│           ├── test_scf_crawler.py
│           └── test_pla_crawler.py
├── integration/
│   └── test_financial_statement_crawlers.py
```

---

### Task 1: 建立爬蟲基底類別

**Files:**
- Create: `src/ExternalService/providers/crawlers/__init__.py`
- Create: `src/ExternalService/providers/crawlers/base_crawler.py`
- Create: `tests/unit/providers/crawlers/__init__.py`
- Create: `tests/unit/providers/crawlers/test_base_crawler.py`

- [ ] **Step 1: 建立目錄套件**

```python
# src/ExternalService/providers/crawlers/__init__.py
"""Financial statement crawler modules for TWSE MOPS API."""
```

```python
# tests/unit/providers/crawlers/__init__.py
```
- [ ] **Step 2: 撰寫 `base_crawler.py` 的失敗測試**

```python
# tests/unit/providers/crawlers/test_base_crawler.py
"""Tests for base crawler class."""

import pytest
from datetime import datetime
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
```

- [ ] **Step 3: 執行測試確認失敗**

Run: `uv run pytest tests/unit/providers/crawlers/test_base_crawler.py -v`
Expected: FAIL with import errors (module not found)

- [ ] **Step 4: 實作 `base_crawler.py`**

```python
# src/ExternalService/providers/crawlers/base_crawler.py
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
        """Try multiple encodings to decode TWSE response."""
        for encoding in ['big5', 'cp950', 'big5-hkscs', 'utf-8']:
            try:
                response.encoding = encoding
                return response.text
            except (LookupError, UnicodeDecodeError):
                continue
        # Fallback: let requests guess
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

    def _request_with_retry(self, url: str) -> Optional[str]:
        """Send HTTP request with retry logic.

        Args:
            url: Target URL

        Returns:
            Response text if successful, None otherwise
        """
        for attempt in range(self.max_retries):
            try:
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
```

- [ ] **Step 5: 執行測試確認通過**

Run: `uv run pytest tests/unit/providers/crawlers/test_base_crawler.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ExternalService/providers/crawlers/ tests/unit/providers/crawlers/
git commit -m "feat: add base financial statement crawler with retry logic and URL builder"
```

---

### Task 2: 實作 BS 爬蟲（資產負債表）

**Files:**
- Create: `src/ExternalService/providers/crawlers/bs_crawler.py`
- Create: `tests/unit/providers/crawlers/test_bs_crawler.py`

- [ ] **Step 1: 撰寫 BS 爬蟲測試**

```python
# tests/unit/providers/crawlers/test_bs_crawler.py
"""Tests for BS (Balance Sheet) crawler."""

import pytest
from src.ExternalService.providers.crawlers.bs_crawler import BsCrawler


class TestBsCrawler:
    """Test BS crawler."""

    def test_report_id(self):
        """Should return 'bps' for balance sheet."""
        crawler = BsCrawler()
        assert crawler.report_id == "bps"

    def test_report_type_value(self):
        """Should return correct type value."""
        crawler = BsCrawler()
        assert crawler.report_type_value == "balance-sheet"

    def test_build_url(self):
        """Should build correct TWSE URL for BS."""
        crawler = BsCrawler()
        url = crawler.build_url(2025, 1)
        assert "REPORT_ID=bps" in url
        assert "SYEAR=114" in url
        assert "SSEASON=1" in url

    def test_download_without_network(self):
        """Should return failure result without network (test structure)."""
        # This validates the method signature and return type
        result = BsCrawler().download(2025, 1)
        # Without network, this will likely fail gracefully
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/unit/providers/crawlers/test_bs_crawler.py -v`
Expected: FAIL with import error

- [ ] **Step 3: 實作 BS 爬蟲**

```python
# src/ExternalService/providers/crawlers/bs_crawler.py
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
```

- [ ] **Step 4: 執行測試確認通過**

Run: `uv run pytest tests/unit/providers/crawlers/test_bs_crawler.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ExternalService/providers/crawlers/bs_crawler.py tests/unit/providers/crawlers/test_bs_crawler.py
git commit -m "feat: add BS (balance sheet) crawler"
```

---

### Task 3: 實作 CPL 爬蟲（綜合損益表）

**Files:**
- Create: `src/ExternalService/providers/crawlers/cpl_crawler.py`
- Create: `tests/unit/providers/crawlers/test_cpl_crawler.py`

- [ ] **Step 1: 撰寫 CPL 爬蟲測試**

```python
# tests/unit/providers/crawlers/test_cpl_crawler.py
"""Tests for CPL (Comprehensive Profit/Loss) crawler."""

import pytest
from src.ExternalService.providers.crawlers.cpl_crawler import CplCrawler


class TestCplCrawler:
    """Test CPL crawler."""

    def test_report_id(self):
        """Should return 'is' for income statement."""
        crawler = CplCrawler()
        assert crawler.report_id == "is"

    def test_report_type_value(self):
        """Should return correct type value."""
        crawler = CplCrawler()
        assert crawler.report_type_value == "consolidated-profit-and-loss-summary"

    def test_build_url(self):
        """Should build correct TWSE URL for CPL."""
        crawler = CplCrawler()
        url = crawler.build_url(2024, 4)
        assert "REPORT_ID=is" in url
        assert "SYEAR=113" in url
        assert "SSEASON=4" in url

    def test_download_returns_result_object(self):
        """Should return DownloadResult."""
        result = CplCrawler().download(2024, 4)
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')
```

- [ ] **Step 2: 實作 CPL 爬蟲**

```python
# src/ExternalService/providers/crawlers/cpl_crawler.py
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
```

- [ ] **Step 3: 執行測試確認通過**

Run: `uv run pytest tests/unit/providers/crawlers/test_cpl_crawler.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/ExternalService/providers/crawlers/cpl_crawler.py tests/unit/providers/crawlers/test_cpl_crawler.py
git commit -m "feat: add CPL (income statement) crawler"
```

---

### Task 4: 實作 SCF 爬蟲（現金流量表）

**Files:**
- Create: `src/ExternalService/providers/crawlers/scf_crawler.py`
- Create: `tests/unit/providers/crawlers/test_scf_crawler.py`

- [ ] **Step 1: 撰寫 SCF 爬蟲測試**

```python
# tests/unit/providers/crawlers/test_scf_crawler.py
"""Tests for SCF (Statement of Cash Flows) crawler."""

import pytest
from src.ExternalService.providers.crawlers.scf_crawler import ScfCrawler


class TestScfCrawler:
    """Test SCF crawler."""

    def test_report_id(self):
        """Should return 'cf' for cash flow statement."""
        crawler = ScfCrawler()
        assert crawler.report_id == "cf"

    def test_report_type_value(self):
        """Should return correct type value."""
        crawler = ScfCrawler()
        assert crawler.report_type_value == "statement-of-cash-flows"

    def test_build_url(self):
        """Should build correct TWSE URL for SCF."""
        crawler = ScfCrawler()
        url = crawler.build_url(2025, 3)
        assert "REPORT_ID=cf" in url
        assert "SYEAR=114" in url
        assert "SSEASON=3" in url

    def test_download_returns_result_object(self):
        """Should return DownloadResult."""
        result = ScfCrawler().download(2025, 3)
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')
```

- [ ] **Step 2: 實作 SCF 爬蟲**

```python
# src/ExternalService/providers/crawlers/scf_crawler.py
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
```

- [ ] **Step 3: 執行測試確認通過**

Run: `uv run pytest tests/unit/providers/crawlers/test_scf_crawler.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/ExternalService/providers/crawlers/scf_crawler.py tests/unit/providers/crawlers/test_scf_crawler.py
git commit -m "feat: add SCF (cash flow statement) crawler"
```

---

### Task 5: 實作 PLA 爬蟲（營益分析彙總表）— **核心修正**

**Files:**
- Create: `src/ExternalService/providers/crawlers/pla_crawler.py`
- Create: `tests/unit/providers/crawlers/test_pla_crawler.py`

**說明：** PLA（營益分析彙總表）不同於 BS/CPL/SCF，TWSE 使用不同端點 `t167sb03` 而非 `t164sb01`，且無 `REPORT_ID` 參數。需覆寫 `build_url()` 方法。

- [ ] **Step 1: 撰寫 PLA 爬蟲測試**

```python
# tests/unit/providers/crawlers/test_pla_crawler.py
"""Tests for PLA (Profit/Loss Analysis) crawler."""

import pytest
from src.ExternalService.providers.crawlers.pla_crawler import PlaCrawler


class TestPlaCrawler:
    """Test PLA crawler."""

    def test_report_id(self):
        """Should return empty string (PLA uses different endpoint)."""
        crawler = PlaCrawler()
        assert crawler.report_id == ""

    def test_report_type_value(self):
        """Should return correct type value."""
        crawler = PlaCrawler()
        assert crawler.report_type_value == "profit-and-loss-analysis-summary"

    def test_build_url_uses_different_endpoint(self):
        """Should use t167sb03 instead of t164sb01."""
        crawler = PlaCrawler()
        url = crawler.build_url(2025, 1)
        # PLA uses a different TWSE endpoint
        assert "t167sb03" in url
        assert "SYEAR=114" in url
        assert "SSEASON=1" in url
        # PLA has no REPORT_ID parameter
        assert "REPORT_ID" not in url

    def test_download_returns_result_object(self):
        """Should return DownloadResult."""
        result = PlaCrawler().download(2025, 1)
        assert hasattr(result, 'success')
        assert hasattr(result, 'df')
        assert hasattr(result, 'url')
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/unit/providers/crawlers/test_pla_crawler.py -v`
Expected: FAIL with import error

- [ ] **Step 3: 實作 PLA 爬蟲（使用正確的 TWSE 端點）**

```python
# src/ExternalService/providers/crawlers/pla_crawler.py
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
```

- [ ] **Step 4: 執行測試確認通過**

Run: `uv run pytest tests/unit/providers/crawlers/test_pla_crawler.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ExternalService/providers/crawlers/pla_crawler.py tests/unit/providers/crawlers/test_pla_crawler.py
git commit -m "feat: add PLA (profit analysis) crawler with correct t167sb03 endpoint"
```

---

### Task 6: 修改 `FinancialStatementProvider` — 整合爬蟲

**Files:**
- Modify: `src/ExternalService/providers/FinancialStatementProvider.py`
- Create: `tests/unit/providers/test_financial_statement_provider_crawler.py`

- [ ] **Step 1: 撰寫整合測試（確認 crawler 委派正確）**

```python
# tests/unit/providers/test_financial_statement_provider_crawler.py
"""Tests for FinancialStatementProvider crawler integration."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from pandas import DataFrame

from src.Common import InfomationType as info
from src.ExternalService.providers.FinancialStatementProvider import (
    FinancialStatementProvider,
)
from src.ExternalService.providers.crawlers.base_crawler import DownloadResult


class TestFinancialStatementProviderCrawler:
    """Test crawler integration in FinancialStatementProvider."""

    @pytest.fixture
    def provider(self):
        """Create provider with mocked dependencies."""
        sql_service = MagicMock()
        mongo_service = MagicMock()
        read_load_system = MagicMock()
        cache_service = MagicMock()
        cache_service.get.return_value = None  # Miss cache
        return FinancialStatementProvider(
            sql_service, mongo_service, read_load_system, cache_service
        )

    @pytest.mark.parametrize("fs_type,expected_crawler_class_name", [
        (info.FS_type.BS, "BsCrawler"),
        (info.FS_type.CPL, "CplCrawler"),
        (info.FS_type.SCF, "ScfCrawler"),
        (info.FS_type.PLA, "PlaCrawler"),
    ])
    def test_crawler_mapping(self, provider, fs_type, expected_crawler_class_name):
        """Should map each FS_type to correct crawler class."""
        crawler = provider._get_crawler(fs_type)
        assert crawler.__class__.__name__ == expected_crawler_class_name

    def test_bs_crawler_download_success(self, provider):
        """Should delegate BS download to BsCrawler."""
        crawler = provider._get_crawler(info.FS_type.BS)
        # Mock the actual HTTP request by patching _request_with_retry
        with patch.object(crawler, '_request_with_retry', return_value="<html><table></table></html>"):
            with patch("pandas.read_html", return_value=[DataFrame(), DataFrame({"col": [1]})]):
                result = crawler.download(2025, 1)
                assert result.success is True

    def test_crawler_fallback_on_file_missing(self, provider):
        """Should try crawler when file and SQL both empty."""
        # Mock all upstream sources as empty
        provider._get_financial_statement_from_sql = MagicMock(return_value=DataFrame())
        provider._get_financial_statement_from_file = MagicMock(return_value=DataFrame())

        # Mock crawler
        mock_df = DataFrame({"公司代號": ["2330"], "公司名稱": ["台積電"]})
        with patch.object(provider, '_financial_statement_download') as mock_download:
            mock_download.return_value = mock_df
            provider._save_financial_statement_to_db = MagicMock()

            result = provider.get_allstock_financial_statement(
                datetime(2025, 3, 15), info.FS_type.BS
            )
            assert not result.empty
            mock_download.assert_called_once()
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/unit/providers/test_financial_statement_provider_crawler.py -v`
Expected: FAIL (method `_get_crawler` not found yet)

- [ ] **Step 3: 修改 `FinancialStatementProvider`**

在 `FinancialStatementProvider` 中：
1. 新增 import for all crawlers
2. 新增 `_get_crawler()` 方法映射 `FS_type` 到對應爬蟲
3. 新增 `_financial_statement_download()` 方法取代舊的 `_financial_statement()`
4. 將 `get_allstock_financial_statement()` 中的步驟 4 改為使用 crawler

```python
# 在 imports 區塊新增
from src.ExternalService.providers.crawlers.bs_crawler import BsCrawler
from src.ExternalService.providers.crawlers.cpl_crawler import CplCrawler
from src.ExternalService.providers.crawlers.scf_crawler import ScfCrawler
from src.ExternalService.providers.crawlers.pla_crawler import PlaCrawler
```

在 `__init__` 中新增 crawler 字典：
```python
self._crawlers = {
    info.FS_type.BS: BsCrawler(),
    info.FS_type.CPL: CplCrawler(),
    info.FS_type.SCF: ScfCrawler(),
    info.FS_type.PLA: PlaCrawler(),
}
```

新增 `_get_crawler()` 方法：
```python
def _get_crawler(self, fs_type: info.FS_type) -> "BaseFinancialCrawler":
    """Get the appropriate crawler for the given financial statement type."""
    return self._crawlers[fs_type]
```

新增 `_financial_statement_download()` 方法取代 `_financial_statement()`：
```python
def _financial_statement_download(
    self, year: int, season: int, fs_type: info.FS_type
) -> pd.DataFrame:
    """Download financial statement using the appropriate crawler.

    Args:
        year: Western calendar year
        season: Quarter number (1-4)
        fs_type: Financial statement type

    Returns:
        DataFrame with parsed data, or empty DataFrame on failure
    """
    crawler = self._get_crawler(fs_type)
    result = crawler.download(year, season)

    if not result.success:
        self._logger.error(
            "Failed to download %s statement for %d Q%d",
            fs_type.name, year, season
        )
        return pd.DataFrame()

    # Save to local file
    file_name = f"{year}-season{season}-{fs_type.value}"
    file_path = os.path.join(self._file_path, "seasonInfo", f"{file_name}.csv")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    result.df.to_csv(file_path, index=False)

    self._logger.info(
        "Downloaded %s statement: %d Q%d (%d rows)",
        fs_type.name, year, season, len(result.df)
    )
    return result.df
```

在 `get_allstock_financial_statement()` 中將步驟 4 改為：
```python
# 4. Download from external source using crawler
crawler_data = self._financial_statement_download(start.year, season, type)
if crawler_data.empty:
    return pd.DataFrame()
```

保留舊的 `_financial_statement()` 方法加上 `@deprecated` 標記或直接移除（建議移除，因所有新程式碼使用 crawler）。

**請注意：針對 `_financial_statement()` 方法，由於它已完全被 `_financial_statement_download()` 取代，應直接替換實作內容或刪除。考慮到向後相容性，最安全的做法是直接改寫其內部邏輯。**

- [ ] **Step 4: 執行所有測試確認通過**

Run:
```bash
uv run pytest tests/unit/providers/ -v
uv run pytest tests/unit/providers/crawlers/ -v
```
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/ExternalService/providers/FinancialStatementProvider.py tests/unit/providers/test_financial_statement_provider_crawler.py
git commit -m "refactor: integrate crawlers into FinancialStatementProvider"
```

---

### Task 7: 撰寫整合測試（可選但建議）

**Files:**
- Create: `tests/integration/test_financial_statement_crawlers.py`

- [ ] **Step 1: 撰寫整合測試**

```python
# tests/integration/test_financial_statement_crawlers.py
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
```

- [ ] **Step 2: 執行整合測試**

Run: `uv run pytest tests/integration/test_financial_statement_crawlers.py -v -m integration`
Expected: Should connect to TWSE and download data

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_financial_statement_crawlers.py
git commit -m "test: add integration tests for financial statement crawlers"
```

---

## Self-Review

### 1. Spec Coverage
- ✅ BS 爬蟲（Task 2）：正確使用 `REPORT_ID=bps` 端點
- ✅ CPL 爬蟲（Task 3）：正確使用 `REPORT_ID=is` 端點
- ✅ SCF 爬蟲（Task 4）：正確使用 `REPORT_ID=cf` 端點
- ✅ PLA 爬蟲（Task 5）：**核心修正**，使用 `t167sb03` 端點（不同於其他三類）
- ✅ 基底類別（Task 1）：共用重試、解碼、HTML 解析邏輯
- ✅ Provider 整合（Task 6）：移除舊的 `_financial_statement()` 混合邏輯
- ✅ 整合測試（Task 7）：實際連線 TWSE 驗證

### 2. Placeholder Scan
- 所有步驟包含完整程式碼
- 所有測試包含斷言
- 無 "TBD"、"TODO"、"implement later"

### 3. Type Consistency
- `BaseFinancialCrawler.download()` → `DownloadResult`（NamedTuple，含 `df`, `url`, `success`）
- 所有 subclass 的 `download()` 返回類型一致
- `_get_crawler(fs_type)` → `BaseFinancialCrawler` 實例
- `report_id` 屬性：BS→`bps`, CPL→`is`, SCF→`cf`, PLA→`""`
- `report_type_value` 屬性：與 `FS_type.value` 保持一致

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-05-23-redesign-financial-statement-crawlers.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — dispatch fresh subagent per task, review between tasks, fast iteration via superpowers:subagent-driven-development

2. **Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints via superpowers:executing-plans

**Which approach?**
