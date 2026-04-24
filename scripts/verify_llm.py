import pandas as pd
from restaurant_rec.config import config
from restaurant_rec.phase2 import UserPreferences, load_catalog
from restaurant_rec.phase3 import get_recommendations
import json

def run_test(name, location, cuisine=None, budget=None, min_rating=None, extras=None):
    print(f"\n=== TEST CASE: {name} ===")
    print(f"Prefs: Loc={location}, Cuisine={cuisine}, Budget={budget}, Rating={min_rating}, Extras={extras}")
    
    prefs = UserPreferences(
        location=location,
        cuisine=cuisine,
        budget_max_inr=budget,
        min_rating=min_rating,
        extras=extras
    )
    
    try:
        # Load catalog
        catalog_df = load_catalog(config.catalog_path)
        
        # Get recommendations
        result = get_recommendations(prefs, catalog_df)
        
        print(f"\nSummary: {result['summary']}")
        print(f"Found {len(result['items'])} recommendations (Shortlist size: {result['meta']['shortlist_size']})")
        
        for item in result['items']:
            print(f"- [{item['rank']}] {item['name']} ({item['rating']} stars, Cost for two: ₹{item['cost_for_two']})")
            print(f"  Explanation: {item['explanation']}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    # Test 1: General Cafe search in BTM
    run_test("Cafe BTM", "BTM", cuisine="Cafe", budget=800, min_rating=4.0)
    
    # Test 2: Italian craving with high rating in HSR
    run_test("High-end Italian", "HSR", cuisine="Italian", min_rating=4.0)

