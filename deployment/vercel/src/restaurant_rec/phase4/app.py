from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import os
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from ..config import config
from ..phase2 import load_catalog, UserPreferences
from ..phase3 import get_recommendations

# Global state for the catalog
catalog_df: pd.DataFrame = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global catalog_df
    # Load catalog once at startup
    try:
        catalog_df = load_catalog(config.catalog_path)
        print(f"Catalog loaded successfully with {len(catalog_df)} rows.")
    except Exception as e:
        print(f"Error loading catalog at startup: {e}")
    yield
    # Cleanup if needed
    catalog_df = None


app = FastAPI(
    title="Restaurant Recommendation API",
    description="AI-powered restaurant recommendations using Groq",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to the Restaurant Recommendation API. UI not found."}


@app.get("/api/v1/localities")
async def get_localities():
    """
    Returns a sorted list of unique localities available in the catalog.
    """
    if catalog_df is None:
        raise HTTPException(status_code=500, detail="Catalog not loaded")
    
    unique_localities = sorted(catalog_df['location'].unique().tolist())
    return {"localities": unique_localities}

@app.get("/api/v1/cuisines")
async def get_cuisines():
    """
    Returns a sorted list of unique cuisines available in the catalog.
    """
    if catalog_df is None:
        raise HTTPException(status_code=500, detail="Catalog not loaded")
    
    all_cuisines = set()
    for c_list in catalog_df['cuisines']:
        if isinstance(c_list, (list, pd.Series, pd.Index)) or hasattr(c_list, '__iter__'):
            all_cuisines.update(c_list)
            
    return {"cuisines": sorted(list(all_cuisines))}


@app.get("/api/v1/restaurant-names")
async def get_restaurant_names(location: str = None):
    """
    Returns a list of unique restaurant names, optionally filtered by location.
    """
    if catalog_df is None:
        raise HTTPException(status_code=500, detail="Catalog not loaded")
    
    df = catalog_df
    if location:
        df = df[df['location'] == location]
    
    return {"names": sorted(df['name'].unique().tolist())}

@app.post("/api/v1/recommend")
async def recommend(prefs: UserPreferences):

    """
    Endpoint to get restaurant recommendations based on user preferences.
    """
    if catalog_df is None:
        raise HTTPException(status_code=500, detail="Catalog not loaded")
    
    try:
        recommendations = get_recommendations(prefs, catalog_df)
        return recommendations
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
