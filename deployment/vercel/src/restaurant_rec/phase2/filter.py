from typing import List, Optional, Dict, Any
import pandas as pd
from pydantic import BaseModel
from .preferences import UserPreferences
from ..config import config

class FilterResult(BaseModel):
    shortlist: List[Dict[str, Any]]
    reason_codes: List[str]
    meta: Dict[str, Any]

def filter_restaurants(catalog_df: pd.DataFrame, prefs: UserPreferences, max_shortlist: int = config.max_shortlist_candidates) -> FilterResult:
    """
    Filter the catalog based on user preferences and return a bounded shortlist.
    """
    df = catalog_df.copy()
    initial_count = len(df)
    reason_codes = []

    # 1. Location filter (Required)
    # We do a case-insensitive exact or substring match on location/city
    if not df.empty and prefs.location:
        loc_lower = prefs.location.lower().strip()
        df = df[df['location'].str.lower() == loc_lower]
        if df.empty:
            reason_codes.append("NO_LOCATION_MATCH")

    # 2. Cuisine filter
    if not df.empty and prefs.cuisine:
        # User might provide a list of cuisines. We want at least one to match.
        cuisines_lower = [c.lower() for c in prefs.cuisine]
        
        def matches_cuisine(row_cuisines):
            if row_cuisines is None or len(row_cuisines) == 0:
                return False
            # Handle list, numpy array, etc.
            row_cuisines_lower = [str(rc).lower() for rc in row_cuisines]
            return any(c in row_c for c in cuisines_lower for row_c in row_cuisines_lower)
            
        df = df[df['cuisines'].apply(matches_cuisine)]

        if df.empty:
            reason_codes.append("NO_CUISINE_MATCH")

    # 3. Rating filter
    if not df.empty and prefs.min_rating is not None:
        # Drop rows with missing rating if min_rating is specified
        df = df[df['rating'].notna() & (df['rating'] >= prefs.min_rating)]
        if df.empty:
            reason_codes.append("NO_RATING_MATCH")

    # 4. Budget filter
    if not df.empty and prefs.budget_max_inr is not None:
        # Drop rows with missing cost if budget is specified
        df = df[df['cost_for_two'].notna() & (df['cost_for_two'] <= prefs.budget_max_inr)]
        if df.empty:
            reason_codes.append("NO_BUDGET_MATCH")

    # 5. Ranking
    if not df.empty:
        # Sort by rating (desc) then votes (desc)
        df = df.sort_values(by=['rating', 'votes'], ascending=[False, False], na_position='last')

    # 6. Truncation
    if not df.empty:
        df = df.head(max_shortlist)

    final_count = len(df)
    
    # Convert dataframe to list of dicts for the shortlist
    # Handle NaN values by converting them to None for JSON serialization
    shortlist_dicts = df.replace({pd.NA: None}).to_dict(orient='records')
    # Extra pass to fix float NaNs and convert ndarrays to lists
    for item in shortlist_dicts:
        if pd.isna(item.get('rating')):
            item['rating'] = None
        if pd.isna(item.get('cost_for_two')):
            item['cost_for_two'] = None
        if pd.isna(item.get('votes')):
            item['votes'] = 0
            
        # Convert ndarray/array to list for JSON serialization
        c = item.get('cuisines')
        if hasattr(c, 'tolist'):
            item['cuisines'] = c.tolist()
        elif not isinstance(c, list) and c is not None:
            item['cuisines'] = list(c)


    return FilterResult(
        shortlist=shortlist_dicts,
        reason_codes=reason_codes,
        meta={
            "initial_catalog_size": initial_count,
            "filtered_size": final_count,
            "max_shortlist_candidates": max_shortlist
        }
    )
