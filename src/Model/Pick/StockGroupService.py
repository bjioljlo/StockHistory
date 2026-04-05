"""
Stock Group Service for Stock Pick Model

Extracted from Model_pick.py - single responsibility: stock group management
"""
from typing import List
import twstock


class StockGroupService:
    """Manages stock group classification"""

    @staticmethod
    def get_all_groups() -> List[str]:
        """
        Get all stock groups from twstock database

        Returns:
            List of unique group names
        """
        groups = []
        for key, value in twstock.codes.items():
            if value.group and value.group not in groups:
                groups.append(value.group)
        return groups