import sys
import os
from pathlib import Path

# Add the root of the deployment folder to sys.path so we can import src
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Override config paths to be relative to the deployment root
os.environ["CATALOG_PATH"] = str(root_dir / "data" / "processed" / "restaurants.parquet")

from src.restaurant_rec.phase4.app import app

# Vercel needs 'app' to be the FastAPI instance
app = app

