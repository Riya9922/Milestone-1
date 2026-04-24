# Phase 2.1: Preference Model and Deterministic Filtering

This phase converts user input into a typed preference object and produces a bounded shortlist of restaurants to pass to the LLM (Phase 3). 

## User Review Required

- **Missing Rating/Cost Handling:** The documentation mentions handling missing ratings or costs. My proposal is to exclude restaurants with a missing rating if a `min_rating` is explicitly requested, and exclude restaurants with missing cost if `budget_max_inr` is explicitly requested. Is this acceptable?
- **Cuisine matching:** The proposal uses case-insensitive substring or exact token matching for cuisines.

## Proposed Changes

### restaurant_rec.phase2

#### [NEW] src/restaurant_rec/phase2/preferences.py
Create a Pydantic model for user input:
- `UserPreferences`
  - `location: str` (Required)
  - `budget_max_inr: Optional[float] = None`
  - `cuisine: Optional[list[str]] = None`
  - `min_rating: Optional[float] = None`
  - `extras: Optional[str] = None`

#### [NEW] src/restaurant_rec/phase2/filter.py
Create the filtering logic and result structures:
- `FilterResult` (Pydantic model) containing the `shortlist` (as a list of dicts or a Pandas DataFrame), `reason_codes` (for empty results), and `meta` (size/timing).
- `filter_restaurants(catalog_df: pd.DataFrame, prefs: UserPreferences, max_shortlist: int = 40) -> FilterResult`:
  1. **Location filter:** Exact case-insensitive match on the `location` field.
  2. **Cuisine filter:** If requested, at least one cuisine must match.
  3. **Rating filter:** Keep if `rating >= min_rating`.
  4. **Budget filter:** Keep if `cost_for_two <= budget_max_inr`.
  5. **Ranking:** Sort remaining by `rating` (descending), then `votes` (descending).
  6. **Truncation:** Take the top `max_shortlist` results.

#### [NEW] src/restaurant_rec/phase2/catalog_loader.py
- `load_catalog(path: Path) -> pd.DataFrame`: A simple utility to load the Parquet file into a Pandas DataFrame using `pd.read_parquet`.

### Tests

#### [NEW] tests/test_phase2.py
- Unit tests to verify the preference validation.
- Unit tests for various filter combinations using a mock/fixture DataFrame.
- Unit tests for edge cases (e.g., zero matches returning `reason_codes` like `NO_LOCATION`).

## Verification Plan

### Automated Tests
- Run `pytest tests/test_phase2.py` to ensure all filtering rules and edge cases work as expected.
- Validate the shortlist size and sorting correctness.

### Manual Verification
- Create a short scratch script to load the actual dataset (`restaurants.parquet`) and run a few filter queries, printing the execution time and shortlist size to ensure latency is predictable.
