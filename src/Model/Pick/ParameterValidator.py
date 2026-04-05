"""
Parameter Validation Service for Stock Pick Model

Extracted from Model_pick.py - single responsibility: parameter validation
"""
import logging
from typing import Dict, Any
from src.Common.Parameter import RecordPickParameter


logger = logging.getLogger(__name__)


class PickParameterValidator:
    """Validates and converts pick parameters"""

    @staticmethod
    def validate(params: RecordPickParameter) -> Dict[str, Any]:
        """
        Validate and extract parameters

        Args:
            params: Input parameters object

        Returns:
            Dictionary of validated and converted values

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            return {
                'GPM': float(params.GPM),
                'OPR': float(params.OPR),
                'EPS': float(params.EPS),
                'RPS': float(params.RPS),
                'monthRP_smoothAVG': int(params.monthRP_smoothAVG),
                'monthRP_UpMpnth': int(params.monthRP_UpMpnth),
                'PBR_low': float(params.PBR_low),
                'PBR_high': float(params.PBR_high),
                'PER_low': float(params.PER_low),
                'PER_high': float(params.PER_high),
                'ROE_low': float(params.ROE_low),
                'ROE_high': float(params.ROE_high),
                'yiled_high': float(params.yiled_high),
                'yiled_low': float(params.yiled_low),
                'OMGR': float(params.OMGR),
                'price_high': float(params.price_high),
                'price_low': float(params.price_low),
                'flash_Day': int(params.flash_Day),
                'record_Day': int(params.record_Day),
                'volum': float(params.volum),
                'PEG_low': float(params.PEG_low),
                'PEG_high': float(params.PEG_high),
                'FCF': float(params.FCF),
                'ROE_up': float(params.ROE),
                'EPS_up': float(params.EPS_up),
                'SRGR': float(params.SRGR),
                'MRGR': float(params.MRGR),
                'BerMA': float(params.BetterMA),
                'Kind': int(params.Kind),
                'avg_vol_multiple': float(params.avg_vol_multiple)
            }
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(f"參數驗證失敗: {e}")
            raise ValueError(f"參數格式錯誤: {e}")