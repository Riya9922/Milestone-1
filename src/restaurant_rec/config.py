from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    raw_data_dir: Path = data_dir / "raw"
    processed_data_dir: Path = data_dir / "processed"
    
    # Dataset config
    hf_dataset_name: str = "ManikaSaini/zomato-restaurant-recommendation"
    hf_dataset_split: str = "train"
    catalog_path: Path = processed_data_dir / "restaurants.parquet"
    max_shortlist_candidates: int = 20
    
    # Groq / LLM config
    groq_api_key: str = ""
    groq_model_id: str = "llama-3.1-8b-instant"
    temperature: float = 0.2


    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global config instance
config = AppConfig()

# Ensure directories exist
config.raw_data_dir.mkdir(parents=True, exist_ok=True)
config.processed_data_dir.mkdir(parents=True, exist_ok=True)
