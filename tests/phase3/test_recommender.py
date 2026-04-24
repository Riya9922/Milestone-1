import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from restaurant_rec.phase2 import UserPreferences
from restaurant_rec.phase3.recommender import get_recommendations

@pytest.fixture
def sample_catalog():
    data = [
        {"id": "1", "name": "Cafe A", "location": "Bangalore", "cuisines": ["Cafe"], "rating": 4.5, "cost_for_two": 500, "votes": 100},
        {"id": "2", "name": "Bistro B", "location": "Bangalore", "cuisines": ["Italian"], "rating": 4.0, "cost_for_two": 1500, "votes": 50},
    ]
    return pd.DataFrame(data)

@patch('restaurant_rec.phase3.recommender.call_gemini')
def test_get_recommendations_success(mock_call, sample_catalog):
    # Setup mock response from Gemini
    mock_call.return_value = {
        "summary": "These are great options.",
        "recommendations": [
            {"restaurant_id": "1", "rank": 1, "explanation": "Top rated cafe."},
            {"restaurant_id": "2", "rank": 2, "explanation": "Authentic Italian."}
        ]
    }
    
    prefs = UserPreferences(location="Bangalore")
    result = get_recommendations(prefs, sample_catalog)
    
    assert result["summary"] == "These are great options."
    assert len(result["items"]) == 2
    assert result["items"][0]["name"] == "Cafe A"
    assert result["items"][0]["explanation"] == "Top rated cafe."
    assert result["items"][0]["rank"] == 1
    assert result["meta"]["shortlist_size"] == 2

@patch('restaurant_rec.phase3.recommender.call_gemini')
def test_get_recommendations_empty_shortlist(mock_call, sample_catalog):
    # If shortlist is empty, call_gemini should not be called
    prefs = UserPreferences(location="Delhi") # No Delhi in sample
    result = get_recommendations(prefs, sample_catalog)
    
    assert "No restaurants matched" in result["summary"]
    assert len(result["items"]) == 0
    assert mock_call.called is False

@patch('restaurant_rec.phase3.recommender.call_gemini')
def test_get_recommendations_partial_llm_response(mock_call, sample_catalog):
    # LLM might return IDs that don't exist (hallucination) or skip some
    mock_call.return_value = {
        "summary": "Only one found.",
        "recommendations": [
            {"restaurant_id": "1", "rank": 1, "explanation": "Good."},
            {"restaurant_id": "999", "rank": 2, "explanation": "Hallucinated."}
        ]
    }
    
    prefs = UserPreferences(location="Bangalore")
    result = get_recommendations(prefs, sample_catalog)
    
    assert len(result["items"]) == 1 # Only 1 is valid
    assert result["items"][0]["id"] == "1"
