import hashlib
import pandas as pd
import numpy as np

def _hash_id(name: str, location: str) -> str:
    s = f"{name}_{location}".lower().strip().encode('utf-8')
    return hashlib.sha256(s).hexdigest()

def clean_rating(rate_str) -> float:
    if pd.isna(rate_str):
        return np.nan
    rate_str = str(rate_str).strip()
    if rate_str in ["NEW", "-", "nan"]:
        return np.nan
    if "/5" in rate_str:
        rate_str = rate_str.split("/")[0].strip()
    try:
        return float(rate_str)
    except ValueError:
        return np.nan

def clean_cost(cost_str) -> float:
    if pd.isna(cost_str):
        return np.nan
    cost_str = str(cost_str).replace(",", "").strip()
    try:
        return float(cost_str)
    except ValueError:
        return np.nan

def parse_cuisines(cuisine_str) -> list:
    if pd.isna(cuisine_str):
        return []
    return [c.strip() for c in str(cuisine_str).split(",") if c.strip()]

def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the raw Hugging Face dataframe into a format
    that aligns with RestaurantRecord canonical schema.
    """
    out = pd.DataFrame()
    
    # 1. name and location
    out["name"] = df["name"].fillna("").astype(str).str.strip()
    out["location"] = df["location"].fillna("").astype(str).str.strip()
    
    # Generate id
    out["id"] = out.apply(lambda row: _hash_id(row["name"], row["location"]), axis=1)
    
    # Cuisines
    if "cuisines" in df.columns:
        out["cuisines"] = df["cuisines"].apply(parse_cuisines)
    else:
        out["cuisines"] = [[] for _ in range(len(df))]
        
    # Rating
    if "rate" in df.columns:
        out["rating"] = df["rate"].apply(clean_rating)
    else:
        out["rating"] = np.nan
        
    # Cost
    if "approx_cost(for two people)" in df.columns:
        out["cost_for_two"] = df["approx_cost(for two people)"].apply(clean_cost)
    else:
        out["cost_for_two"] = np.nan
        
    # Votes
    if "votes" in df.columns:
        out["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)
    else:
        out["votes"] = 0
        
    # Address
    if "address" in df.columns:
        out["address"] = df["address"].astype(str)
    else:
        out["address"] = None
        
    # Raw features (combine multiple useful fields)
    features = []
    if "rest_type" in df.columns:
        features.append(df["rest_type"].fillna("").astype(str))
    if "dish_liked" in df.columns:
        features.append(df["dish_liked"].fillna("").astype(str))
        
    if features:
        # Join the text fields with a separator
        out["raw_features"] = pd.concat(features, axis=1).apply(
            lambda x: " | ".join([v for v in x if v and str(v) != "nan"]), axis=1
        )
        # Empty string should be None
        out["raw_features"] = out["raw_features"].replace("", None)
    else:
        out["raw_features"] = None

    return out
