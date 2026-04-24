System context
Purpose: Combine a real restaurant dataset with user preferences and an LLM to produce ranked recommendations with natural-language explanations.
High-level flow:
Offline or on-demand: load and normalize restaurant records.
Online: accept preferences → filter catalog to a shortlist → prompt Groq (Phase 3) → return structured UI payload.
Non-goals (unless you add them later): user accounts, live Zomato scraping, training custom embedding models.

Phase 1 — Foundation, dataset contract, and catalog
1.1 Objectives
Establish a single source of truth for restaurant data after Hugging Face ingest.
Define a canonical schema so filtering, prompting, and UI do not depend on raw column names.
Make ingestion repeatable (same command → same artifact).
1.2 Dataset source
Primary: ManikaSaini/zomato-restaurant-recommendation via datasets library or export script.
1.3 Canonical schema (recommended fields)
Map HF columns to internal names (exact mapping depends on dataset columns; validate after first load):
Internal field
Role
id
Stable string or hash (if missing, derive from name+location)
name
Restaurant name
location / city
For location filter (normalize: trim, title case, alias map e.g. "Bengaluru" → "Bangalore" if needed)
cuisines
List of strings or single pipe/comma-separated field parsed to list
rating
Float 0–5 (or dataset scale; document and normalize)
cost_for_two or approx_cost
Numeric or categorical; derive budget_tier: low | medium | high
votes / review_count
Optional; use for tie-breaking in shortlist
address or locality
Optional; richer prompts and UI
raw_features
Optional blob for “family-friendly” style hints if present in text columns

1.4 Components
Component
Responsibility
Ingestion script
Download/load split, select columns, rename to canonical schema
Validators
Row-level checks (rating range, required name/location), quarantine or drop bad rows with counts logged
Transformers
Parse cuisines, normalize city, compute budget_tier from rules (e.g. quantiles or fixed thresholds)
Catalog store
Versioned file: Parquet (preferred), SQLite, or JSON Lines for small prototypes

Implementation lives under restaurant_rec.phase1 (ingest, transform, validate, schema) and scripts/ingest_zomato.py.
1.5 Artifacts and layout (suggested)
data/
  raw/              # optional: snapshot of downloaded slice
  processed/
    restaurants.parquet   # or restaurants.db
scripts/
  ingest_zomato.py   # or notebooks/01_ingest.ipynb for exploration-only phase
src/restaurant_rec/
  config.py          # shared: AppConfig, paths, dataset + filter tuning
  phase1/            # catalog ingest + schema
  phase2/            # preferences, load catalog, deterministic filter
  phase3/            # Groq prompts, JSON parse, `recommend()` orchestration

1.6 Configuration
Path to catalog file, encoding, and threshold constants (rating scale, budget cutoffs) in config.yaml or environment variables.
1.7 Exit criteria
Documented schema with example row (JSON).
One command reproduces processed/restaurants.* from HF.
Documented row counts before/after cleaning and top reasons for drops.

Phase 2 — Preference model and deterministic filtering
2.1 Objectives
Convert user input into a typed preference object.
Produce a bounded shortlist (e.g. 20–50 venues) that is small enough for one LLM call but diverse enough to rank.
2.2 Preference model (API / domain)
Structured input (align with problem statement):
Field
Type
Notes
location
string
Required for first version; fuzzy match optional later
budget
enum
low | medium | high
cuisine
string or list
Match against cuisines (substring or token match)
min_rating
float
Hard filter: rating >= min_rating
extras
string (optional)
Free text: “family-friendly”, “quick service”; used in LLM prompt and optional keyword boost

Optional extensions: max_results_shortlist, dietary, neighborhood.
2.3 Filtering pipeline (order matters)
Location filter: Exact or normalized match on city / location.
Cuisine filter: At least one cuisine matches user selection (case-insensitive).
Rating filter: rating >= min_rating; if too few results, optional relax step (document policy: e.g. lower min by 0.5 once).
Budget filter: Match budget_tier to user budget.
Ranking for shortlist: Sort by rating desc, then votes desc; take top N.
2.4 Component boundaries
Module (package path)
Responsibility
restaurant_rec.phase2.preferences
Pydantic validation, defaults (UserPreferences)
restaurant_rec.phase2.filter
filter_restaurants(catalog_df, prefs) -> FilterResult
restaurant_rec.phase2.catalog_loader
Load Parquet into a DataFrame at startup

2.5 Edge cases
Zero matches: Return empty shortlist with reason codes (NO_LOCATION, NO_CUISINE, etc.) for UI messaging.
Missing rating/cost: Exclude from strict filters or treat as unknown with explicit rules in docs.
2.6 Exit criteria
Unit tests for filter combinations and empty results.
Shortlist size and latency predictable (log timing for 100k rows if applicable).

Phase 3 — LLM integration: prompt contract and orchestration
Phase 3 uses Groq (GroqCloud / Groq API) as the LLM for ranking, explanations, and optional summaries. The Groq API key is loaded from a .env file (see §3.6); never commit real keys to version control.
3.1 Objectives
Given preferences + shortlist JSON, produce ordered recommendations with per-item explanations and optional overall summary.
Keep behavior testable (template version, structured output where possible).
Call Groq over HTTP with the official Groq Python SDK or OpenAI-compatible client pointed at Groq’s base URL, using credentials supplied via environment variables populated from .env.
3.2 Inputs to the LLM
System message: Role (expert recommender), constraints (only recommend from provided list; respect min rating and budget; if list empty, say so).
User message: Serialized shortlist (compact JSON or markdown table) + preference summary + extras text.
3.3 Output contract
Preferred: JSON from the model (with schema validation and repair retry):
{
  "summary": "string",
  "recommendations": [
    {
      "restaurant_id": "string",
      "rank": 1,
      "explanation": "string"
    }
  ]
}

Fallback: parse markdown numbered list if JSON fails; log and degrade gracefully.
3.4 Prompt engineering checklist
Include only restaurants from the shortlist (by id) to reduce hallucination.
Ask for top K (e.g. 5) with one paragraph max per explanation.
Instruct to cite concrete attributes (cuisine, rating, cost) from the data.
3.5 Orchestration service
Step
Action
1
Build shortlist (Phase 2)
2
If empty, return structured empty response (skip LLM or single small call explaining no matches)
3
Render prompt from template + data
4
Call Groq API with timeout and max tokens
5
Parse/validate response; on failure, retry once with “JSON only” reminder or fall back to heuristic order

3.6 Configuration
API key (Groq): Keep the Groq API key in a .env file in the project root (or the directory the app loads env from). Use python-dotenv or your framework’s equivalent so values are available as environment variables at runtime. Add .env to .gitignore and commit only a .env.example (or README snippet) listing required variable names with empty or placeholder values.
Typical variable name: GROQ_API_KEY (confirm against Groq API documentation when implementing).
Non-secret settings: Model id (e.g. llama3-70b-8192 or mixtral-8x7b-32768), temperature (low for consistency), max_tokens, and display top_k can live in config.yaml or additional env vars as needed.
3.7 Exit criteria
Golden-file or manual eval sheet for ~10 preference profiles.
Documented latency and token usage for typical shortlist sizes.

Phase 4 — Application layer: API and presentation
4.1 Objectives
Expose a single recommendation endpoint (or CLI) that returns everything the UI needs.
Render Restaurant Name, Cuisine, Rating, Estimated Cost, AI explanation per row.
4.2 Backend API (recommended shape)
POST /api/v1/recommend
Request body: JSON matching Preferences (Phase 2).
Response body includes AI summary, ranked items with merge metadata, and shortlist stats.

GET /api/v1/localities
Returns a sorted list of all unique localities in the catalog for UI dropdown population.

GET /api/v1/cuisines
Returns a sorted list of all unique cuisines available in the filtered catalog for UI dropdown population.


Implementation note: Merge LLM output with catalog rows by restaurant_id to fill cuisine, rating, and cost for display (do not trust the LLM for numeric facts).
Backend (implemented): restaurant_rec.phase4.app — FastAPI app with CORS enabled. Run from repo root after pip install -e .:
uvicorn restaurant_rec.phase4.app:app --reload
Open http://127.0.0.1:8000/ for the browser UI (web/). Interactive API: http://127.0.0.1:8000/docs.
Loads config.yaml and paths.processed_catalog at startup; GROQ_API_KEY from .env applies to recommend calls.
4.3 UI — basic web app (end-to-end)
Web app
Premium SPA — Form with dynamic dropdowns, "Mood Chips" for extra details, loading states, and result cards with restaurant/food imagery.
Backend API
FastAPI serving static files from `src/restaurant_rec/phase4/static/` and exposing JSON endpoints.

CLI
Optional; curl or /docs
Notebook
Teaching/demo only

4.4 Cross-cutting concerns
CORS if SPA on different origin.
Rate limiting if exposed publicly.
Input validation return 422 with field errors.
4.5 Exit criteria
Backend: POST /api/v1/recommend returns structured summary, items, and meta; validation errors return 422; empty filter outcomes return 200 with empty items and a clear summary.
Browser: user opens /, submits preferences → sees summary and ranked cards (or empty-state message).
Empty and error states copy-reviewed for clarity.

Improvements (tracked)
The following were implemented in code, API, UI, and phase-wise-architecture.md:
Locality & Cuisine dropdowns — GET /api/v1/localities and GET /api/v1/cuisines return distinct catalog values; the web UI uses these for precise filtering.
Mood Chips — Interactive UI buttons for "Romantic Date", "Family Dinner", etc., that automatically populate the additional preferences field.
Visual Recommendations — Restaurant cards include contextual food and cafe imagery (via Unsplash) to enhance the user experience.
Numeric budget — User preference is budget_max_inr (max approximate cost for two in INR). Phase 2 keeps rows with known cost_for_two ≤ budget_max_inr. Groq prompts describe this value instead of low/medium/high tiers.
Fixed shortlist size — max_results_shortlist was removed from user input. filter.max_shortlist_candidates in config.yaml caps rows passed to the LLM (default 40).
LLM Provider — Reverted from Gemini to Groq (Llama 3.3 70B) for superior structured output and lower latency.


Phase 5 — Hardening, observability, and quality
5.1 Objectives
Improve reliability, debuggability, and iterative prompt/dataset updates without breaking clients.
5.2 Caching
Key: hash of (preferences, shortlist content hash, prompt_version, model).
TTL or LRU for repeated queries in demos.
5.3 Logging and metrics
Structured logs: shortlist_size, duration_filter_ms, duration_llm_ms, outcome (success / empty / error).
Avoid logging full prompts if they contain sensitive data; truncate or redact.
5.4 Testing strategy
Layer
Tests
Filter
Unit tests, property tests optional
Prompt
Snapshot of rendered template with fixture data
API
Contract tests for /recommend
LLM
Marked optional integration tests with recorded responses

5.5 Exit criteria
Runbook: how to refresh data, bump prompt version, rotate API keys.
Basic load/latency note for expected concurrency.

Phase 6 — Deployment
6.1 Architecture Overview
The system is decoupled into a Python API (Backend) and a React/Next.js or Static SPA (Frontend) to allow independent scaling and optimized delivery.

6.2 Backend (Streamlit / Python Hosting)
- **Platform:** Streamlit Community Cloud (or similar Python-optimized environment).
- **Function:** Serves the FastAPI application and the logic for the Zomato data processing.
- **Data Persistence:** Processed Parquet files are bundled with the deployment or loaded from cloud storage.
- **Secrets:** GROQ_API_KEY is managed via Streamlit's Secret Management.

6.3 Frontend (Vercel)
- **Platform:** Vercel.
- **Function:** Hosts the enhanced "Zomato-Style" UI (React/Next.js components).
- **Integration:** Communicates with the Backend API via environment variables (BACKEND_URL).
- **Features:** Automated CI/CD, Edge caching for static assets, and premium performance.


