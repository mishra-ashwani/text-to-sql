from app.models.schemas import ColumnDefinition, SchemaInput, TableDefinition
from app.services.prompt_builder import build_prompts, schema_to_ddl


def _sample_schema():
    return SchemaInput(
        tables=[
            TableDefinition(
                table_name="users",
                columns=[
                    ColumnDefinition(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    ColumnDefinition(name="name", data_type="VARCHAR(100)", is_nullable=False),
                    ColumnDefinition(name="email", data_type="VARCHAR(255)"),
                ],
            ),
            TableDefinition(
                table_name="orders",
                columns=[
                    ColumnDefinition(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    ColumnDefinition(name="user_id", data_type="INT", foreign_key="users.id"),
                    ColumnDefinition(name="amount", data_type="DECIMAL(10,2)", is_nullable=False),
                ],
            ),
        ],
        sql_dialect="postgresql",
    )


def test_schema_to_ddl_contains_tables():
    ddl = schema_to_ddl(_sample_schema())
    assert "CREATE TABLE users" in ddl
    assert "CREATE TABLE orders" in ddl


def test_schema_to_ddl_primary_key():
    ddl = schema_to_ddl(_sample_schema())
    assert "id INT PRIMARY KEY" in ddl


def test_schema_to_ddl_not_null():
    ddl = schema_to_ddl(_sample_schema())
    assert "name VARCHAR(100) NOT NULL" in ddl


def test_schema_to_ddl_foreign_key():
    ddl = schema_to_ddl(_sample_schema())
    assert "REFERENCES users(id)" in ddl


def test_build_prompts_returns_two_strings():
    sys_prompt, user_prompt = build_prompts(_sample_schema(), "Show all users")
    assert "postgresql" in sys_prompt.lower()
    assert "Show all users" in user_prompt
    assert "CREATE TABLE" in user_prompt


def test_build_prompts_dialect():
    schema = _sample_schema()
    schema.sql_dialect = "mysql"
    sys_prompt, _ = build_prompts(schema, "test")
    assert "mysql" in sys_prompt.lower()
