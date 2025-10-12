from enum import Enum

from TGetExternalData import TGetExternalData
from GetExternalDataTest import GetExternalDataTest
from IGetExternalData import IGetExternalData


class ExternalDataTypeEnum(Enum):
    Normal = (0,)
    Test = 1

class ExternalDataFactory:
    @staticmethod
    def Get_instance(
        type: ExternalDataTypeEnum = ExternalDataTypeEnum.Normal,
    ) -> IGetExternalData:
        if type == ExternalDataTypeEnum.Test:
            return GetExternalDataTest()
        else:
            return TGetExternalData()