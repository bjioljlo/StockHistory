"""
Financial utilities module
==========================

Financial calculation functions for trading and investment analysis.
"""

from typing import Optional


def calculate_total_with_fees(
    stock_price: Optional[float],
    amount: Optional[int],
    is_buy: bool = True,
    fee_percent: float = 0.1425,
    apply_fees: bool = True
) -> float:
    """
    Calculate total transaction value including handling fee and transaction tax.
    
    Args:
        stock_price: Price per stock share
        amount: Number of shares
        is_buy: True for buy transaction, False for sell transaction
        fee_percent: Brokerage handling fee percentage (default: 0.1425%)
        apply_fees: Whether to apply fees (False returns raw value)
        
    Returns:
        Total transaction value after fees
    """
    if stock_price is None or amount is None:
        return 0.0
    
    base_value = stock_price * amount
    
    if not apply_fees:
        return base_value
    
    if not is_buy:
        # Sell transaction includes both fee and 0.3% transaction tax
        total_fee = (fee_percent + 0.3) / 100
        return base_value * (1 - total_fee)
    else:
        # Buy transaction only includes handling fee
        return base_value * (1 + fee_percent / 100)


def calculate_max_shares(available_money: float, stock_price: float) -> int:
    """
    Calculate maximum number of shares that can be purchased with available money,
    including transaction fees.
    
    Args:
        available_money: Total money available for purchase
        stock_price: Current price per share
        
    Returns:
        Maximum number of whole shares that can be purchased
    """
    if stock_price <= 0:
        return 0
    
    # Calculate effective price including 0.1425% fee
    effective_price = stock_price * 1.001425
    return int(available_money // effective_price)


def smooth_data(data, window_size: int):
    """
    Apply moving average smoothing to data series.
    
    Args:
        data: pandas DataFrame or Series to smooth
        window_size: Number of periods for rolling average
        
    Returns:
        Smoothed data with same type as input
    """
    return data.rolling(window_size, min_periods=window_size).mean()