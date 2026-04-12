from enum import Enum

from src.ExternalService.TGetExternalData import TGetExternalData
from src.ExternalService.GetExternalDataTest import GetExternalDataTest
from src.ExternalService.IGetExternalData import IGetExternalData
from src.ExternalService.MockGetExternalData import MockGetExternalData
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.SqlService import SqlService


class ExternalDataTypeEnum(Enum):
    Normal = 0
    Test = 1

class ExternalDataFactory:
    def __init__(self,
        sql_service: SqlService,
        mongo_service: MongoService,
        read_load_system: ReadLoadSystem,
        cache_service=None):
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._cache_service = cache_service
    def Get_instance(self,
        type: ExternalDataTypeEnum = ExternalDataTypeEnum.Test,
    ) -> IGetExternalData:
        if type == ExternalDataTypeEnum.Normal:
            return TGetExternalData(sql_service=self._sql_service, mongo_service=self._mongo_service,
                                   read_load_system=self._read_load_system, cache_service=self._cache_service)
        elif type == ExternalDataTypeEnum.Test:
            # GetExternalDataTest is incomplete and missing abstract method implementations
            # Falling back to Mock which implements full interface correctly
            return MockGetExternalData(sql_service=self._sql_service, mongo_service=self._mongo_service,
                                       read_load_system=self._read_load_system, cache_service=self._cache_service)
        else:
            # Default fallback to Mock for safety
            return MockGetExternalData(sql_service=self._sql_service, mongo_service=self._mongo_service,
                                       read_load_system=self._read_load_system, cache_service=self._cache_service)

