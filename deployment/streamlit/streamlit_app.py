import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.restaurant_rec.phase4.app import app
import uvicorn
import threading

st.set_page_config(page_title="Zomato AI Backend", page_icon="🚀")

st.title("🚀 Restaurant Rec AI Backend")
st.info("This Streamlit app hosts the FastAPI backend for the Zomato AI Recommendation engine.")

# Run FastAPI in a background thread
def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if "api_thread" not in st.session_state:
    st.session_state.api_thread = threading.Thread(target=run_api, daemon=True)
    st.session_state.api_thread.start()
    st.success("FastAPI Backend started on port 8000")

st.write("### API Status")
st.write("- **Endpoint:** `POST /api/v1/recommend`")
st.write("- **Documentation:** [Swagger UI](/docs) (Note: May require proxy configuration on Streamlit Cloud)")

st.divider()
st.write("### Environment Information")
st.write(f"**Project Root:** `{project_root}`")
st.write(f"**Python Version:** `{sys.version}`")

# Verification: Try to load catalog
from src.restaurant_rec.phase2 import load_catalog
from src.restaurant_rec.config import config
try:
    df = load_catalog(config.catalog_path)
    st.success(f"Successfully loaded catalog with {len(df)} rows.")
except Exception as e:
    st.error(f"Error loading catalog: {e}")

