import pandas as pd
from typing import Dict, Any, List
from ..phase2 import UserPreferences, filter_restaurants
from .prompts import SYSTEM_PROMPT, render_user_prompt
from .client import call_llm

def get_recommendations(prefs: UserPreferences, catalog_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Orchestrates the recommendation flow: filtering -> LLM ranking -> response formatting.
    """
    # 1. Filter the catalog to get a shortlist (Phase 2)
    filter_result = filter_restaurants(catalog_df, prefs)
    
    if not filter_result.shortlist:
        return {
            "summary": "No restaurants matched your criteria. Try relaxing your filters.",
            "items": [],
            "meta": {
                "shortlist_size": 0,
                "reason_codes": filter_result.reason_codes
            }
        }

    # 2. Render the prompt for the LLM
    user_prompt = render_user_prompt(prefs.model_dump(), filter_result.shortlist)
    
    # 3. Call the LLM (Phase 3)
    llm_response = call_llm(user_prompt, SYSTEM_PROMPT)

    
    # 4. Merge LLM recommendations with catalog data for display
    # We want to return the full restaurant details, not just what the LLM gave us
    shortlist_lookup = {item['id']: item for item in filter_result.shortlist}
    
    final_items = []
    for rec in llm_response.get('recommendations', []):
        rid = rec.get('restaurant_id')
        if rid in shortlist_lookup:
            item = shortlist_lookup[rid].copy()
            item['explanation'] = rec.get('explanation', '')
            item['rank'] = rec.get('rank', 0)
            final_items.append(item)
            
    # Sort by rank
    final_items.sort(key=lambda x: x.get('rank', 99))

    return {
        "summary": llm_response.get('summary', ''),
        "items": final_items,
        "meta": {
            "shortlist_size": len(filter_result.shortlist),
            "filtered_count": filter_result.meta.get('filtered_size', 0)
        }
    }
