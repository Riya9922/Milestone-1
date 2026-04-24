# Phase 2.1: Preference Model & Deterministic Filtering Walkthrough

I've successfully implemented Phase 2.1 from the architecture doc. This phase is responsible for mapping user preferences to a shortlist of valid restaurants to be processed by the LLM in Phase 3.

## What was implemented

1. **Preference Model**: I created `UserPreferences` using Pydantic in `src/restaurant_rec/phase2/preferences.py`. It accepts strict types with validation for `location`, `budget_max_inr`, `cuisine`, `min_rating`, and `extras`. It supports flexible string formats for `cuisine` (e.g., `"Cafe, Bakery"`).
2. **Filtering Logic**: I built the core pipeline `filter_restaurants` in `src/restaurant_rec/phase2/filter.py`. The pipeline processes rules sequentially:
   - Filters exact case-insensitive matches for the required `location`.
   - Filters partial matches for any specified `cuisine`.
   - Strips restaurants missing ratings/costs if those criteria are specifically requested via `min_rating` or `budget_max_inr`.
   - Ranks the valid candidates descending by `rating`, then `votes`.
   - Truncates to `max_shortlist_candidates` (default: 40).
3. **Catalog Loader**: Created a simple Parquet loader `load_catalog` in `src/restaurant_rec/phase2/catalog_loader.py`.
4. **Export Module**: Added an `__init__.py` to neatly export the objects so the rest of the application can import `UserPreferences` and `filter_restaurants` directly from `restaurant_rec.phase2`.

## Validation Results

I wrote a comprehensive test suite of 11 tests in `tests/test_phase2.py` which simulate various constraints, exact matches, case-insensitivity, missing data fields, and edge cases like returning correct "reason codes" for empty results. 

The tests run successfully using `pytest`:

```
tests\test_phase2.py ...........                                         [100%]
============================= 11 passed in 8.21s ==============================
```

> [!TIP]
> The module is now ready to be imported into the main application logic, taking us to Phase 3 (LLM orchestration) or directly mapping the API inputs to Phase 2 outputs.
