"""
ExternalDataFactory - 外部資料工廠 + 轉送器

繼承 datafetcher_core 實作，覆寫 Get_instance() 為實例方法。
"""
from datafetcher_core.external_data_factory import (
    ExternalDataFactory as _ExternalDataFactory,
    ExternalDataTypeEnum,
)
from datafetcher_core.external_data_facade import TGetExternalData


class ExternalDataFactory(_ExternalDataFactory):
    """外部資料工廠 - 繼承 package 版，提供實例方法 Get_instance()"""

    def Get_instance(self, type: ExternalDataTypeEnum = ExternalDataTypeEnum.Normal):
        if self._instance is None:
            self._instance = TGetExternalData(
                self._sql_service,
                self._mongo_service,
                self._read_load_system,
                self._cache_service,
            )
        return self._instance
