import json
from typing import List, Dict, Any

SYSTEM_PROMPT = """You are an expert restaurant recommender. 
Given a user's preferences and a shortlist of restaurant candidates, your job is to:
1. Rank the top 5 restaurants that best match the user's needs.
2. Provide a brief, persuasive explanation for each recommendation, citing specific data like cuisine, rating, or cost.
3. Provide a concise overall summary of why these choices were made.

CONSTRAINTS:
- ONLY recommend restaurants from the provided shortlist. Do NOT hallucinate new venues.
- Respect the user's budget and rating preferences.
- If the shortlist is empty or no restaurants match the criteria, say so in the summary.
- Respond ONLY in valid JSON format.
"""

USER_PROMPT_TEMPLATE = """
USER PREFERENCES:
- Location: {location}
- Cuisine: {cuisine}
- Max Budget (INR): {budget_max_inr}
- Min Rating: {min_rating}
- Additional info: {extras}

SHORTLIST CANDIDATES (JSON):
{shortlist_json}

Please return the recommendations in this JSON schema:
{{
  "summary": "string",
  "recommendations": [
    {{
      "restaurant_id": "string",
      "rank": integer,
      "explanation": "string"
    }}
  ]
}}
"""

def render_user_prompt(prefs_dict: Dict[str, Any], shortlist: List[Dict[str, Any]]) -> str:
    """
    Render the user prompt by inserting preferences and shortlist JSON.
    """
    # Prune shortlist to essential fields to save tokens
    pruned_shortlist = []
    for item in shortlist:
        pruned_shortlist.append({
            "id": item.get('id'),
            "name": item.get('name'),
            "cuisines": item.get('cuisines'),
            "rating": item.get('rating'),
            "cost": item.get('cost_for_two'),
            "features": item.get('raw_features')
        })
    
    # Compact JSON for the shortlist
    shortlist_json = json.dumps(pruned_shortlist, separators=(',', ':'))

    
    return USER_PROMPT_TEMPLATE.format(
        location=prefs_dict.get('location', 'Any'),
        cuisine=prefs_dict.get('cuisine', 'Any'),
        budget_max_inr=prefs_dict.get('budget_max_inr', 'Not specified'),
        min_rating=prefs_dict.get('min_rating', 'Not specified'),
        extras=prefs_dict.get('extras', 'None'),
        shortlist_json=shortlist_json
    )
