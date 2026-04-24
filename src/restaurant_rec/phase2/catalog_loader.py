import pandas as pd
from pathlib import Path

def load_catalog(path: Path) -> pd.DataFrame:
    """
    Load the restaurant catalog Parquet file into a Pandas DataFrame.
    """
    if not path.exists():
        raise FileNotFoundError(f"Catalog file not found at {path}")
    return pd.read_parquet(path)
