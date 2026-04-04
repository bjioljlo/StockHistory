"""
Stock utilities module
======================

Stock classification and validation functions.
"""

from typing import Union
import logging

logger = logging.getLogger(__name__)


# Stock classification constants
EXCLUDED_STOCKS = [2025]
ETF_LIST = ["00692", "00878", "00646", "00881", "00733"]


def is_excluded_stock(stock_id: Union[str, int]) -> bool:
    """
    Check if stock is in excluded list.
    
    Args:
        stock_id: Stock number or code
        
    Returns:
        True if stock should be excluded
    """
    try:
        stock_num = int(stock_id)
        return stock_num in EXCLUDED_STOCKS
    except (ValueError, TypeError):
        logger.debug(f"Invalid stock ID format: {stock_id}")
        return False


def is_etf_stock(stock_code: Union[str, int]) -> bool:
    """
    Check if stock is an ETF.
    
    Args:
        stock_code: Stock code or number
        
    Returns:
        True if stock is in ETF list
    """
    try:
        code_str = str(stock_code)
        return code_str in ETF_LIST
    except (ValueError, TypeError):
        logger.debug(f"Invalid ETF code format: {stock_code}")
        return False