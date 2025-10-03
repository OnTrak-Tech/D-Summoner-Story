"""
Unit tests for shared utility functions.
Tests data processing, statistics calculation, and helper functions.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from shared.utils import (
    calculate_kda, calculate_win_rate, get_month_year_from_timestamp,
    calculate_improvement_trend, calculate_consistency_score,
    validate_region, sanitize_summoner_name, safe_divide,
    format_lambda_response
)
from shared.models import MonthlyData, RiotMatch, RiotParticipant


class TestUtilityFunctions:
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
        # January 1, 2024 timestamp (in milliseconds)
        timestamp = 1704067200000
        month, year = get_month_year_from_timestamp(timestamp)
        
        assert month == "January"
        assert year == 2024
    
    def test_calculate_improvement_trend_improving(self):
        """Test improvement trend calculation with improving performance"""
        monthly_data = [
            MonthlyData("January", 2024, 10, 4, 6, 40.0, 50, 60, 70, 2.0),
            MonthlyData("February", 2024, 10, 6, 4, 60.0, 60, 50, 80, 2.8),
            MonthlyData("March", 2024, 10, 8, 2, 80.0, 70, 40, 90, 4.0)
        ]
        
        trend = calculate_improvement_trend(monthly_data)
        assert trend > 0  # Should be positive for improvement
    
    def test_calculate_improvement_trend_declining(self):
        """Test improvement trend calculation with declining performance"""
        monthly_data = [
            MonthlyData("January", 2024, 10, 8, 2, 80.0, 70, 40, 90, 4.0),
            MonthlyData("February", 2024, 10, 6, 4, 60.0, 60, 50, 80, 2.8),
            MonthlyData("March", 2024, 10, 4, 6, 40.0, 50, 60, 70, 2.0)
        ]
        
        trend = calculate_improvement_trend(monthly_data)
        assert trend < 0  # Should be negative for decline
    
    def test_calculate_improvement_trend_single_month(self):
        """Test improvement trend with single month (should return 0)"""
        monthly_data = [
            MonthlyData("January", 2024, 10, 6, 4, 60.0, 60, 50, 80, 2.8)
        ]
        
        trend = calculate_improvement_trend(monthly_data)
        assert trend == 0.0
    
    def test_calculate_consistency_score_perfect(self):
        """Test consistency score with perfect consistency"""
        monthly_data = [
            MonthlyData("January", 2024, 10, 6, 4, 60.0, 60, 50, 80, 2.5),
            MonthlyData("February", 2024, 10, 6, 4, 60.0, 60, 50, 80, 2.5),
            MonthlyData("March", 2024, 10, 6, 4, 60.0, 60, 50, 80, 2.5)
        ]
        
        score = calculate_consistency_score(monthly_data)
        assert score == 100.0
    
    def test_calculate_consistency_score_variable(self):
        """Test consistency score with variable performance"""
        monthly_data = [
            MonthlyData("January", 2024, 10, 6, 4, 60.0, 60, 50, 80, 1.0),
            MonthlyData("February", 2024, 10, 6, 4, 60.0, 60, 50, 80, 3.0),
            MonthlyData("March", 2024, 10, 6, 4, 60.0, 60, 50, 80, 2.0)
        ]
        
        score = calculate_consistency_score(monthly_data)
        assert 0 <= score <= 100
        assert score < 100  # Should be less than perfect
    
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
    
    def test_sanitize_summoner_name(self):
        """Test summoner name sanitization"""
        assert sanitize_summoner_name("  TestSummoner  ") == "TestSummoner"
        assert sanitize_summoner_name("Test Summoner") == "TestSummoner"
        assert sanitize_summoner_name("Test  Summoner") == "TestSummoner"
    
    def test_safe_divide_normal(self):
        """Test safe division with normal values"""
        result = safe_divide(10, 2)
        assert result == 5.0
    
    def test_safe_divide_zero_denominator(self):
        """Test safe division with zero denominator"""
        result = safe_divide(10, 0)
        assert result == 0.0
    
    def test_safe_divide_custom_default(self):
        """Test safe division with custom default value"""
        result = safe_divide(10, 0, default=-1.0)
        assert result == -1.0
    
    def test_format_lambda_response_success(self):
        """Test Lambda response formatting for success"""
        response = format_lambda_response(200, {"message": "success"})
        
        assert response["statusCode"] == 200
        assert "headers" in response
        assert response["headers"]["Content-Type"] == "application/json"
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        
        body = response["body"]
        assert '"message": "success"' in body
    
    def test_format_lambda_response_error(self):
        """Test Lambda response formatting for error"""
        response = format_lambda_response(400, {"error": "Bad Request"})
        
        assert response["statusCode"] == 400
        body = response["body"]
        assert '"error": "Bad Request"' in body
    
    def test_format_lambda_response_custom_headers(self):
        """Test Lambda response formatting with custom headers"""
        custom_headers = {"X-Custom-Header": "test-value"}
        response = format_lambda_response(200, {"data": "test"}, custom_headers)
        
        assert response["headers"]["X-Custom-Header"] == "test-value"
        assert response["headers"]["Content-Type"] == "application/json"  # Should still have default


class TestDataProcessing:
    """Test cases for data processing functions"""
    
    def create_mock_match(self, match_id: str, summoner_wins: bool, 
                         kills: int = 5, deaths: int = 3, assists: int = 8) -> RiotMatch:
        """Helper to create mock match data"""
        participant = RiotParticipant(
            summoner_id="test_summoner",
            champion_id=1,
            champion_name="TestChampion",
            kills=kills,
            deaths=deaths,
            assists=assists,
            win=summoner_wins,
            game_duration=1800,  # 30 minutes
            total_damage_dealt=15000,
            gold_earned=12000,
            cs_total=150
        )
        
        return RiotMatch(
            match_id=match_id,
            game_creation=1704067200000,  # Jan 1, 2024
            game_duration=1800,
            game_mode="CLASSIC",
            game_type="MATCHED_GAME",
            queue_id=420,
            participants=[participant]
        )
    
    @patch('shared.utils.process_match_statistics')
    def test_process_match_statistics_mock(self, mock_process):
        """Test that process_match_statistics can be mocked"""
        # This is a placeholder test to ensure the function can be imported and mocked
        mock_process.return_value = MagicMock()
        
        from shared.utils import process_match_statistics
        result = process_match_statistics([], "test_puuid")
        
        mock_process.assert_called_once_with([], "test_puuid")


if __name__ == "__main__":
    pytest.main([__file__])