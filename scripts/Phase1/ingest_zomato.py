import sys
import logging
from pathlib import Path
from datasets import load_dataset
import pyarrow as pa
import pyarrow.parquet as pq

# Add src to python path to import restaurant_rec
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

from restaurant_rec.config import config
from restaurant_rec.phase1.transformers import transform_dataframe
from restaurant_rec.phase1.validators import validate_dataframe

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info(f"Loading dataset: {config.hf_dataset_name} ({config.hf_dataset_split})")
    try:
        # Load the dataset from Hugging Face
        dataset = load_dataset(config.hf_dataset_name, split=config.hf_dataset_split)
        
        # Convert to pandas dataframe
        logger.info("Converting to pandas DataFrame...")
        raw_df = dataset.to_pandas()
        
        logger.info(f"Loaded {len(raw_df)} rows. Starting transformation...")
        # Transform to canonical schema
        transformed_df = transform_dataframe(raw_df)
        
        logger.info("Starting validation...")
        # Validate and clean
        cleaned_df, drop_reasons = validate_dataframe(transformed_df)
        
        # Ensure schema column order and drop any unexpected columns
        expected_columns = [
            "id", "name", "location", "cuisines", "rating", 
            "cost_for_two", "votes", "address", "raw_features"
        ]
        cleaned_df = cleaned_df[expected_columns]
        
        # Convert to pyarrow table
        logger.info("Saving to Parquet format...")
        table = pa.Table.from_pandas(cleaned_df, preserve_index=False)
        
        # Write to Parquet
        pq.write_table(table, config.catalog_path)
        logger.info(f"Successfully saved {len(cleaned_df)} rows to {config.catalog_path}")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
