import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database.db import Base, engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def sample_schema():
    return {
        "tables": [
            {
                "table_name": "users",
                "columns": [
                    {"name": "id", "data_type": "INT", "is_primary_key": True, "is_nullable": False},
                    {"name": "name", "data_type": "VARCHAR(100)", "is_primary_key": False, "is_nullable": False},
                ],
            }
        ],
        "sql_dialect": "postgresql",
    }


@pytest.mark.asyncio
async def test_save_and_list_schemas(sample_schema):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/schemas", json={"name": "test_schema", "schema_input": sample_schema})
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "test_schema"
        assert data["id"] is not None

        res = await client.get("/api/schemas")
        assert res.status_code == 200
        schemas = res.json()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "test_schema"


@pytest.mark.asyncio
async def test_get_schema_by_id(sample_schema):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/schemas", json={"name": "s1", "schema_input": sample_schema})
        schema_id = res.json()["id"]

        res = await client.get(f"/api/schemas/{schema_id}")
        assert res.status_code == 200
        assert res.json()["name"] == "s1"


@pytest.mark.asyncio
async def test_get_schema_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/schemas/9999")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_schema(sample_schema):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/schemas", json={"name": "to_delete", "schema_input": sample_schema})
        schema_id = res.json()["id"]

        res = await client.delete(f"/api/schemas/{schema_id}")
        assert res.status_code == 200

        res = await client.get(f"/api/schemas/{schema_id}")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_generate_empty_schema():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/generate", json={
            "schema_input": {"tables": [], "sql_dialect": "postgresql"},
            "requirement": "Show all users"
        })
        assert res.status_code == 422  # pydantic validation: min_length=1


@pytest.mark.asyncio
async def test_generate_empty_requirement(sample_schema):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/generate", json={
            "schema_input": sample_schema,
            "requirement": ""
        })
        assert res.status_code == 422  # pydantic validation: min_length=1


@pytest.mark.asyncio
async def test_history_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/history")
        assert res.status_code == 200
        assert res.json() == []


@pytest.mark.asyncio
async def test_delete_history_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.delete("/api/history/9999")
        assert res.status_code == 404
