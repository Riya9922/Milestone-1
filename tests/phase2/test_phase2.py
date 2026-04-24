import pytest
import pandas as pd
from restaurant_rec.phase2 import UserPreferences, filter_restaurants, FilterResult

@pytest.fixture
def sample_catalog():
    data = [
        {
            "id": "1", "name": "Cafe A", "location": "Bangalore", 
            "cuisines": ["Cafe", "Bakery"], "rating": 4.5, "cost_for_two": 500, "votes": 100
        },
        {
            "id": "2", "name": "Bistro B", "location": "Bangalore", 
            "cuisines": ["Italian", "Pizza"], "rating": 4.0, "cost_for_two": 1500, "votes": 50
        },
        {
            "id": "3", "name": "Diner C", "location": "Delhi", 
            "cuisines": ["North Indian", "Fast Food"], "rating": 3.8, "cost_for_two": 600, "votes": 200
        },
        {
            "id": "4", "name": "Eatery D", "location": "Bangalore", 
            "cuisines": ["South Indian", "Cafe"], "rating": 4.8, "cost_for_two": 400, "votes": 500
        },
        {
            "id": "5", "name": "Missing Data E", "location": "Bangalore", 
            "cuisines": ["Cafe"], "rating": None, "cost_for_two": None, "votes": 0
        }
    ]
    return pd.DataFrame(data)

def test_preferences_cuisine_parsing():
    prefs = UserPreferences(location="Bangalore", cuisine="Cafe, Bakery")
    assert prefs.cuisine == ["Cafe", "Bakery"]

def test_filter_location_exact(sample_catalog):
    prefs = UserPreferences(location="Bangalore")
    result = filter_restaurants(sample_catalog, prefs)
    assert len(result.shortlist) == 4
    assert result.meta["filtered_size"] == 4
    assert not result.reason_codes

def test_filter_location_case_insensitive(sample_catalog):
    prefs = UserPreferences(location="bangalore")
    result = filter_restaurants(sample_catalog, prefs)
    assert len(result.shortlist) == 4

def test_filter_no_location_match(sample_catalog):
    prefs = UserPreferences(location="Mumbai")
    result = filter_restaurants(sample_catalog, prefs)
    assert len(result.shortlist) == 0
    assert "NO_LOCATION_MATCH" in result.reason_codes

def test_filter_cuisine(sample_catalog):
    prefs = UserPreferences(location="Bangalore", cuisine=["Italian"])
    result = filter_restaurants(sample_catalog, prefs)
    assert len(result.shortlist) == 1
    assert result.shortlist[0]["name"] == "Bistro B"

def test_filter_cuisine_case_insensitive_substring(sample_catalog):
    prefs = UserPreferences(location="Bangalore", cuisine=["cafe"])
    result = filter_restaurants(sample_catalog, prefs)
    assert len(result.shortlist) == 3
    # Eatery D, Cafe A, Missing Data E
    names = [r["name"] for r in result.shortlist]
    assert "Eatery D" in names
    assert "Cafe A" in names

def test_filter_no_cuisine_match(sample_catalog):
    prefs = UserPreferences(location="Bangalore", cuisine=["Mexican"])
    result = filter_restaurants(sample_catalog, prefs)
    assert len(result.shortlist) == 0
    assert "NO_CUISINE_MATCH" in result.reason_codes

def test_filter_rating(sample_catalog):
    prefs = UserPreferences(location="Bangalore", min_rating=4.2)
    result = filter_restaurants(sample_catalog, prefs)
    # Should keep Eatery D (4.8) and Cafe A (4.5)
    assert len(result.shortlist) == 2
    names = [r["name"] for r in result.shortlist]
    assert "Eatery D" in names
    assert "Cafe A" in names
    # Ensure ranked by rating desc
    assert result.shortlist[0]["name"] == "Eatery D"
    assert result.shortlist[1]["name"] == "Cafe A"

def test_filter_budget(sample_catalog):
    prefs = UserPreferences(location="Bangalore", budget_max_inr=1000)
    result = filter_restaurants(sample_catalog, prefs)
    # Should keep Cafe A (500) and Eatery D (400)
    # Bistro B is 1500, Missing Data E has None
    assert len(result.shortlist) == 2
    names = [r["name"] for r in result.shortlist]
    assert "Eatery D" in names
    assert "Cafe A" in names

def test_filter_combined(sample_catalog):
    prefs = UserPreferences(
        location="Bangalore",
        cuisine="Cafe",
        min_rating=4.0,
        budget_max_inr=600
    )
    result = filter_restaurants(sample_catalog, prefs)
    # Cafe A and Eatery D
    assert len(result.shortlist) == 2

def test_filter_truncation(sample_catalog):
    prefs = UserPreferences(location="Bangalore")
    result = filter_restaurants(sample_catalog, prefs, max_shortlist=2)
    assert len(result.shortlist) == 2
    assert result.meta["max_shortlist_candidates"] == 2
