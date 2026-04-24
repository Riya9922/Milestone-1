import pandas as pd
from restaurant_rec.config import config
from restaurant_rec.phase2 import load_catalog

catalog_df = load_catalog(config.catalog_path)
print("Unique Locations (Top 20):")
print(catalog_df['location'].unique()[:20])

print("\nUnique Cuisines (Top 20):")
# Flat list of all cuisines
all_cuisines = set()
for c_list in catalog_df['cuisines']:
    if isinstance(c_list, list):
        all_cuisines.update(c_list)
print(sorted(list(all_cuisines))[:20])

print(f"\nTotal rows: {len(catalog_df)}")
