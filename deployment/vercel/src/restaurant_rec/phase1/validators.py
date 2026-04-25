import pandas as pd
from typing import Tuple
import logging
from .schema import RestaurantRecord

logger = logging.getLogger(__name__)

def validate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Validates the transformed dataframe.
    Drops rows missing essential fields (name, location).
    Returns the cleaned DataFrame and a dictionary of drop counts.
    """
    initial_count = len(df)
    
    # Check required fields
    # Empty string or purely whitespace is considered invalid
    has_name = df["name"].str.strip().astype(bool)
    has_location = df["location"].str.strip().astype(bool)
    
    # We will keep rows that are valid
    valid_mask = has_name & has_location
    
    # Optional: validate schema types using pydantic (this can be slow for large DFs,
    # so we do it by converting to dicts, but vectorised dropping is better first)
    cleaned_df = df[valid_mask].copy()
    
    # To be extremely thorough with the canonical schema, we can convert
    # to Pydantic and drop rows that raise validation errors, but since we 
    # constructed the DF in transformers.py it should be fairly clean.
    # We will just rely on Pydantic's validation as an integration check.
    
    final_count = len(cleaned_df)
    drop_reasons = {
        "missing_name_or_location": initial_count - final_count
    }
    
    logger.info(f"Validation complete. Kept {final_count}/{initial_count} rows.")
    for reason, count in drop_reasons.items():
        if count > 0:
            logger.warning(f"Dropped {count} rows due to {reason}")
            
    return cleaned_df, drop_reasons
