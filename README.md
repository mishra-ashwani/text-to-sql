# Text to SQL

A web application that converts natural language requirements into SQL queries. Define your database schema, describe what you need in plain English, and get a validated SQL query back.

## Features

- **Schema Builder** — visually define tables, columns, keys, and relationships
- **DDL Import** — paste existing `CREATE TABLE` statements to auto-populate
- **SQL Generation** — powered by GPT-4o via LangChain
- **Validation** — syntax checking via sqlglot + schema reference verification
- **History** — saved schemas and query history with persistence
- **Dark UI** — responsive single-page app with Tailwind CSS

## Tech Stack

Python 3.11+ | FastAPI | LangChain + OpenAI | SQLAlchemy + SQLite | Tailwind CSS

## Quick Start

```bash
# Clone and setup
cd text-to-sql
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

# Run
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000

## Configuration

All settings are configurable via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | Your OpenAI API key |
| `DATABASE_URL` | `sqlite+aiosqlite:///./text_to_sql.db` | Database connection string |
| `DEFAULT_SQL_DIALECT` | `postgresql` | Default SQL dialect |
| `LLM_MODEL` | `gpt-4o` | OpenAI model to use |
| `LLM_TIMEOUT` | `30` | LLM request timeout in seconds |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS origins |
| `RATE_LIMIT` | `20/minute` | Rate limit for /api/generate |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Generate SQL from schema + requirement |
| POST | `/api/schemas` | Save a schema |
| GET | `/api/schemas` | List saved schemas |
| GET | `/api/schemas/{id}` | Get a schema |
| DELETE | `/api/schemas/{id}` | Delete a schema |
| GET | `/api/history` | Query generation history |
| DELETE | `/api/history/{id}` | Delete history entry |

Interactive API docs available at `/docs` (Swagger UI).

## Running Tests

```bash
source venv/bin/activate
pip install pytest pytest-asyncio httpx
python -m pytest tests/ -v
```

## Project Structure

```
text-to-sql/
├── app/
│   ├── main.py              # FastAPI app, CORS, rate limiting
│   ├── config.py            # Settings via pydantic-settings
│   ├── routes/
│   │   ├── schema.py        # Schema CRUD endpoints
│   │   └── query.py         # SQL generation endpoint
│   ├── services/
│   │   ├── prompt_builder.py # Schema → DDL → LLM prompt
│   │   ├── llm_service.py   # LangChain LLM integration
│   │   └── sql_validator.py # SQL validation and formatting
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   └── database/
│       ├── db.py            # Async SQLAlchemy engine
│       └── models.py        # ORM models
├── frontend/
│   └── index.html           # Single-page app
├── tests/                   # Test suite
├── requirements.txt
└── .env.example
```
