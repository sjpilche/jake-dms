# CLAUDE.md — Jake-DMS Agent Doctrine

## Project
CFO Command Center for Dhar Mann Studios ($78M creator-led media company).
Pre-interview demo (Build 1) → Production agents (Build 2) → Executive summary (Build 3).

## Stack
Python 3.11 | Poetry | Pydantic v2 strict | SQLAlchemy | Streamlit | httpx | plotly | loguru

## Rules
1. No print(). Use `from loguru import logger`.
2. All models: Pydantic v2 with `model_config = ConfigDict(strict=True)`.
3. Type hints on every function signature. No `Any` unless wrapping external API JSON.
4. Financial math: Decimal where precision matters, deterministic — never LLM-generated.
5. Every external dependency has a mock mode controlled by env var or config flag.
6. Fail loudly: raise, don't swallow. Log the error, then raise.
7. Tests for every calculation function. No test? No merge.
8. All config via pydantic-settings. Never read os.environ directly.

## YouTube Channel
- Channel ID: UC_hK9fOxyy_TM8FJGXIyG8Q (Dhar Mann Studios)
- API: YouTube Data API v3 (API key, public data only for Build 1)
- Endpoints: channels.list, search.list, videos.list

## Demo Mode
- `DEMO_MODE=true` (default) uses SQLite mock data + cached YouTube responses
- `DEMO_MODE=false` hits live APIs (requires valid keys)
- Cached responses stored in data/ directory as JSON

## Mock Intacct Data
SQLite database seeded by src/demo/mock_data.py. Tables mirror Sage Intacct GL structure.
Revenue: $78M/yr. Expenses: $58M/yr. 26% operating margin. 18 months of history.

## Running
```bash
poetry install
poetry run streamlit run src/demo/app.py
```

## Testing
```bash
poetry run pytest
poetry run mypy src/
```
