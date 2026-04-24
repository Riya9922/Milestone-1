import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_localities():
    print("\n--- Testing /api/v1/localities ---")
    resp = requests.get(f"{BASE_URL}/api/v1/localities")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Success! Found {len(data['localities'])} localities.")
        print(f"Sample: {data['localities'][:5]}")
    else:
        print(f"Error: {resp.status_code} - {resp.text}")

def test_recommend():
    print("\n--- Testing /api/v1/recommend ---")
    payload = {
        "location": "BTM",
        "cuisine": "Cafe",
        "budget_max_inr": 800,
        "min_rating": 4.0
    }
    resp = requests.post(f"{BASE_URL}/api/v1/recommend", json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Summary: {data.get('summary')}")
        print(f"Recommendations: {len(data.get('items', []))}")
        for item in data.get('items', [])[:2]:
            print(f"- {item['name']} (Rank {item['rank']}): {item['explanation']}")
    else:
        print(f"Error: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    try:
        test_localities()
        test_recommend()
    except Exception as e:
        print(f"Failed to connect to server: {e}")
