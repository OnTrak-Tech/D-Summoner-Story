"""
Simplified unit tests for shared utility functions.
Tests core utility functions without complex dependencies.
"""

import pytest
import sys
import os
from datetime import datetime, timezone

# Add the shared modules to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from shared.utils import (
    calculate_kda, 
    calculate_win_rate, 
    get_month_year_from_timestamp,
    safe_divide,
    chunk_list,
    sanitize_summoner_name,
    validate_region
)


class TestUtilsSimple:
    """Test cases for utility functions"""
    
    def test_calculate_kda_normal(self):
        """Test KDA calculation with normal values"""
        kda = calculate_kda(10, 5, 15)
        assert kda == 5.0
    
    def test_calculate_kda_zero_deaths(self):
        """Test KDA calculation with zero deaths"""
        kda = calculate_kda(10, 0, 15)
        assert kda == 25.0
    
    def test_calculate_kda_zero_kills_assists(self):
        """Test KDA calculation with zero kills and assists"""
        kda = calculate_kda(0, 5, 0)
        assert kda == 0.0
    
    def test_calculate_kda_all_zero(self):
        """Test KDA calculation with all zeros"""
        kda = calculate_kda(0, 0, 0)
        assert kda == 0.0
    
    def test_calculate_win_rate_normal(self):
        """Test win rate calculation with normal values"""
        win_rate = calculate_win_rate(7, 10)
        assert win_rate == 70.0
    
    def test_calculate_win_rate_zero_games(self):
        """Test win rate calculation with zero games"""
        win_rate = calculate_win_rate(0, 0)
        assert win_rate == 0.0
    
    def test_calculate_win_rate_perfect(self):
        """Test win rate calculation with 100% wins"""
        win_rate = calculate_win_rate(10, 10)
        assert win_rate == 100.0
    
    def test_get_month_year_from_timestamp(self):
        """Test month/year extraction from timestamp"""
        # January 1, 2024 00:00:00 UTC
        timestamp = 1704067200000
        month, year = get_month_year_from_timestamp(timestamp)
        assert month == "January"
        assert year == 2024
    
    def test_safe_divide_normal(self):
        """Test safe division with normal values"""
        result = safe_divide(10, 2)
        assert result == 5.0
    
    def test_safe_divide_zero_denominator(self):
        """Test safe division with zero denominator"""
        result = safe_divide(10, 0)
        assert result == 0.0
    
    def test_safe_divide_custom_default(self):
        """Test safe division with custom default"""
        result = safe_divide(10, 0, default=-1.0)
        assert result == -1.0
    
    def test_chunk_list_normal(self):
        """Test list chunking with normal values"""
        lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunks = chunk_list(lst, 3)
        expected = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
        assert chunks == expected
    
    def test_chunk_list_empty(self):
        """Test list chunking with empty list"""
        chunks = chunk_list([], 3)
        assert chunks == []
    
    def test_chunk_list_single_chunk(self):
        """Test list chunking where chunk size is larger than list"""
        lst = [1, 2, 3]
        chunks = chunk_list(lst, 5)
        assert chunks == [[1, 2, 3]]
    
    def test_sanitize_summoner_name(self):
        """Test summoner name sanitization"""
        # Test with spaces
        result = sanitize_summoner_name("Test Summoner")
        assert result == "TestSummoner"
        
        # Test with leading/trailing spaces
        result = sanitize_summoner_name("  TestName  ")
        assert result == "TestName"
        
        # Test with multiple spaces
        result = sanitize_summoner_name("Test   Multiple   Spaces")
        assert result == "TestMultipleSpaces"
    
    def test_validate_region_valid(self):
        """Test region validation with valid regions"""
        assert validate_region("na1") == True
        assert validate_region("euw1") == True
        assert validate_region("kr") == True
    
    def test_validate_region_invalid(self):
        """Test region validation with invalid regions"""
        assert validate_region("invalid") == False
        assert validate_region("") == False
        assert validate_region("NA1") == False  # Case sensitive


if __name__ == "__main__":
    pytest.main([__file__])