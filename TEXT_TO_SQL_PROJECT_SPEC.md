# Text-to-SQL Web Application — Project Specification

## Overview

Build a web application where users can convert natural language requirements into SQL queries. Users provide their database table structures, write a requirement in plain English, and the system generates the corresponding SQL query using an LLM.

---

## Tech Stack

| Layer          | Technology                                      |
| -------------- | ----------------------------------------------- |
| Language       | Python 3.11+                                    |
| Backend        | FastAPI + Uvicorn                               |
| LLM            | OpenAI GPT-4o via LangChain                     |
| SQL Validation | sqlparse, sqlglot                               |
| Data Models    | Pydantic v2                                     |
| Database       | SQLite (via SQLAlchemy + aiosqlite) for history  |
| Frontend       | HTML + Tailwind CSS + Vanilla JS (single page)  |
| Config         | python-dotenv                                   |

---

## Project Structure

```
text-to-sql/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point, CORS, mount static
│   ├── config.py                # Settings via pydantic-settings + .env
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── schema.py            # Schema CRUD endpoints
│   │   └── query.py             # SQL generation endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── prompt_builder.py    # Schema JSON → DDL → full LLM prompt
│   │   ├── llm_service.py       # LangChain LLM integration
│   │   └── sql_validator.py     # SQL validation and formatting
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic request/response models
│   └── database/
│       ├── __init__.py
│       ├── db.py                # SQLAlchemy async engine + session
│       └── models.py            # SQLAlchemy ORM models (history, saved schemas)
├── frontend/
│   └── index.html               # Single-page frontend (Tailwind + JS)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Requirements (requirements.txt)

```
fastapi==0.115.0
uvicorn==0.30.6
langchain==0.3.7
langchain-openai==0.2.6
sqlparse==0.5.1
sqlglot==25.8.1
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
sqlalchemy==2.0.35
aiosqlite==0.20.0
```

---

## Environment Variables (.env.example)

```
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=sqlite+aiosqlite:///./text_to_sql.db
DEFAULT_SQL_DIALECT=postgresql
```

---

## Module Specifications

### 1. Config (`app/config.py`)

Use `pydantic-settings` to load environment variables.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str = "sqlite+aiosqlite:///./text_to_sql.db"
    default_sql_dialect: str = "postgresql"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### 2. Pydantic Models (`app/models/schemas.py`)

Define these request/response models:

#### Column Model

```python
class ColumnDefinition(BaseModel):
    name: str                          # e.g. "id", "email"
    data_type: str                     # e.g. "INT", "VARCHAR(255)"
    is_primary_key: bool = False
    is_nullable: bool = True
    default_value: Optional[str] = None
    foreign_key: Optional[str] = None  # e.g. "users.id"
```

#### Table Model

```python
class TableDefinition(BaseModel):
    table_name: str
    columns: List[ColumnDefinition]
```

#### Schema Input (full database schema)

```python
class SchemaInput(BaseModel):
    tables: List[TableDefinition]
    sql_dialect: Optional[str] = "postgresql"  # postgresql, mysql, sqlite
```

#### Query Generation Request

```python
class QueryRequest(BaseModel):
    schema_input: SchemaInput
    requirement: str                   # Natural language requirement
```

#### Query Generation Response

```python
class QueryResponse(BaseModel):
    sql_query: str                     # The generated SQL
    formatted_query: str               # Pretty-printed version
    is_valid: bool                     # Whether sqlglot validation passed
    validation_errors: Optional[List[str]] = None
    explanation: Optional[str] = None  # LLM's explanation of the query
```

#### Saved Schema (for persistence)

```python
class SavedSchema(BaseModel):
    id: Optional[int] = None
    name: str
    schema_input: SchemaInput
    created_at: Optional[datetime] = None
```

#### Query History Entry

```python
class QueryHistoryEntry(BaseModel):
    id: Optional[int] = None
    requirement: str
    generated_sql: str
    schema_name: Optional[str] = None
    created_at: Optional[datetime] = None
```

---

### 3. Prompt Builder (`app/services/prompt_builder.py`)

This module converts the structured schema JSON into a well-formatted prompt for the LLM.

#### Responsibilities

- Convert `SchemaInput` → DDL (CREATE TABLE statements)
- Handle foreign key relationships
- Construct the full system prompt + user prompt

#### System Prompt Template

```
You are an expert SQL query generator. You ONLY generate valid {dialect} SQL queries.

Rules:
1. ONLY use tables and columns defined in the provided schema. Never invent tables or columns.
2. Return ONLY the SQL query — no explanations, no markdown code blocks.
3. Use proper JOIN syntax when multiple tables are involved.
4. Use aliases for readability when joining tables.
5. If the requirement is ambiguous, make reasonable assumptions and note them.
6. Optimize the query for performance where possible.
7. Use the correct SQL dialect syntax for {dialect}.
```

#### User Prompt Template

```
Database Schema:
{ddl_statements}

Requirement: {user_requirement}

Generate the SQL query:
```

#### DDL Generation Logic

For each table in `SchemaInput.tables`, generate a `CREATE TABLE` statement:

```sql
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT REFERENCES users(id),
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 4. LLM Service (`app/services/llm_service.py`)

#### Responsibilities

- Initialize LangChain `ChatOpenAI` with GPT-4o
- Send the constructed prompt and return the SQL response
- Handle errors and retries

#### Implementation Notes

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,          # Deterministic output for SQL
            api_key=settings.openai_api_key
        )

    async def generate_sql(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = await self.llm.ainvoke(messages)
        return response.content.strip()
```

- Use `temperature=0` for consistent, deterministic SQL output
- Use async `ainvoke` for non-blocking calls in FastAPI

---

### 5. SQL Validator (`app/services/sql_validator.py`)

#### Responsibilities

- Format generated SQL using `sqlparse`
- Validate SQL syntax using `sqlglot`
- Cross-check that all referenced tables/columns exist in the user's schema

#### Implementation Notes

```python
import sqlparse
import sqlglot

def format_sql(sql: str) -> str:
    return sqlparse.format(sql, reindent=True, keyword_case='upper')

def validate_sql(sql: str, dialect: str = "postgres") -> tuple[bool, list[str]]:
    errors = []
    try:
        parsed = sqlglot.parse(sql, read=dialect)
        if not parsed:
            errors.append("Could not parse SQL")
    except sqlglot.errors.ParseError as e:
        errors.append(str(e))
    return (len(errors) == 0, errors)

def check_schema_references(sql: str, schema: SchemaInput) -> list[str]:
    """Check that all tables/columns in the SQL exist in the schema."""
    warnings = []
    # Extract table names from schema
    valid_tables = {t.table_name.lower() for t in schema.tables}
    valid_columns = {}
    for t in schema.tables:
        valid_columns[t.table_name.lower()] = {c.name.lower() for c in t.columns}

    # Parse SQL and extract referenced tables/columns using sqlglot
    # Flag any that don't exist in the provided schema
    # ... implementation here
    return warnings
```

---

### 6. Database Layer (`app/database/`)

#### `db.py` — Async SQLAlchemy Setup

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

#### `models.py` — ORM Models

Two tables:

- `saved_schemas` — id, name, schema_json (TEXT), created_at
- `query_history` — id, requirement (TEXT), generated_sql (TEXT), schema_name, is_valid (BOOL), created_at

---

### 7. API Routes

#### Schema Routes (`app/routes/schema.py`)

| Method | Endpoint             | Description                    |
| ------ | -------------------- | ------------------------------ |
| POST   | `/api/schemas`       | Save a new schema              |
| GET    | `/api/schemas`       | List all saved schemas         |
| GET    | `/api/schemas/{id}`  | Get a specific saved schema    |
| DELETE | `/api/schemas/{id}`  | Delete a saved schema          |

#### Query Routes (`app/routes/query.py`)

| Method | Endpoint             | Description                          |
| ------ | -------------------- | ------------------------------------ |
| POST   | `/api/generate`      | Generate SQL from schema + requirement |
| GET    | `/api/history`       | Get query generation history          |
| DELETE | `/api/history/{id}`  | Delete a history entry               |

#### POST `/api/generate` — Core Endpoint Flow

```
1. Receive QueryRequest (schema + requirement)
2. Call prompt_builder.build_prompt(schema, requirement, dialect)
3. Call llm_service.generate_sql(system_prompt, user_prompt)
4. Call sql_validator.format_sql(raw_sql)
5. Call sql_validator.validate_sql(formatted_sql, dialect)
6. Call sql_validator.check_schema_references(formatted_sql, schema)
7. Save to query_history
8. Return QueryResponse
```

---

### 8. FastAPI Main (`app/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import schema, query
from app.database.db import init_db

app = FastAPI(title="Text to SQL", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schema.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

@app.on_event("startup")
async def startup():
    await init_db()
```

---

### 9. Frontend (`frontend/index.html`)

Single-page HTML app using Tailwind CSS (via CDN) and vanilla JavaScript.

#### UI Sections

1. **Schema Builder Panel (Left/Top)**
   - Form to add tables: table name input + dynamic column rows
   - Each column row: name, type (dropdown), primary key (checkbox), nullable (checkbox), foreign key (optional input)
   - "Add Column" button, "Add Table" button
   - Visual list of added tables with edit/delete
   - "Paste DDL" option: textarea where user can paste raw CREATE TABLE SQL
   - SQL dialect selector dropdown (PostgreSQL, MySQL, SQLite)
   - "Save Schema" button with name input

2. **Query Input Panel (Center/Right)**
   - Textarea for natural language requirement
   - Example placeholder: "Show all users who placed more than 3 orders in the last month"
   - "Generate SQL" button (primary action)
   - Loading spinner during generation

3. **Result Panel (Below)**
   - Syntax-highlighted SQL output (use a `<pre>` block with basic highlighting)
   - Validation status badge (Valid / Invalid)
   - Any validation warnings listed
   - "Copy to Clipboard" button
   - Optional: LLM explanation toggle

4. **Sidebar/Drawer**
   - Saved schemas list (load on click)
   - Query history list (load on click to see past results)

#### Tailwind Design Notes

- Dark theme preferred (gray-900 background, gray-800 cards)
- Use monospace font for SQL output
- Responsive: stack panels vertically on mobile
- Accent color: indigo-500 for buttons and highlights

#### JavaScript Logic

- All API calls via `fetch()` to FastAPI backend
- Schema builder dynamically adds/removes table and column rows
- On "Generate SQL" click: collect schema JSON + requirement → POST to `/api/generate`
- Display formatted SQL in result panel
- Copy button uses `navigator.clipboard.writeText()`

---

## Sample Test Data

Use this schema for testing:

```sql
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT REFERENCES users(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'pending'
);

CREATE TABLE order_items (
    id INT PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);
```

### Sample Requirements to Test

1. "Show all users from Mumbai who placed orders in the last 30 days"
2. "Find the top 5 most ordered products by quantity"
3. "Get the total revenue per category for orders with status 'completed'"
4. "List users who have never placed an order"
5. "Show monthly order count and revenue for the year 2025"
6. "Find products that are out of stock but appear in at least one order"

---

## Build Order (Step by Step)

Follow this sequence for development:

1. **Project setup** — Create directory structure, install dependencies, create `.env`
2. **Config** — Implement `app/config.py`
3. **Pydantic models** — Implement `app/models/schemas.py`
4. **Prompt builder** — Implement `app/services/prompt_builder.py` with tests
5. **LLM service** — Implement `app/services/llm_service.py`, test with hardcoded schema
6. **SQL validator** — Implement `app/services/sql_validator.py`
7. **Database layer** — Implement `app/database/db.py` and `app/database/models.py`
8. **API routes** — Implement `/api/generate` first, then schema CRUD, then history
9. **Main app** — Wire everything together in `app/main.py`
10. **Frontend** — Build `frontend/index.html` with schema builder + query UI
11. **Testing** — Test with sample data from above
12. **Polish** — Error handling, loading states, edge cases

---

## Error Handling

Handle these cases gracefully:

- **Empty schema**: Return 400 with message "At least one table is required"
- **Empty requirement**: Return 400 with message "Requirement cannot be empty"
- **LLM API failure**: Return 503 with message "AI service temporarily unavailable"
- **LLM returns non-SQL**: Detect and retry once, then return error
- **Invalid SQL generated**: Return the query anyway but mark `is_valid: false` with errors
- **Rate limiting**: Implement basic rate limiting on `/api/generate` (e.g., 20 requests/minute)

---

## Future Enhancements (Out of Scope for V1)

- Support for Anthropic Claude as alternative LLM
- Query execution against a live database connection
- Multi-turn conversation (refine queries iteratively)
- Schema import from live database connection string
- Export query history as SQL file
- User authentication and multi-user support
- Support for complex SQL features: CTEs, window functions, subqueries
