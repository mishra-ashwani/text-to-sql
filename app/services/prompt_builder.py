from app.models.schemas import SchemaInput

SYSTEM_PROMPT_TEMPLATE = """You are an expert SQL query generator. You ONLY generate valid {dialect} SQL queries.

Rules:
1. ONLY use tables and columns defined in the provided schema. Never invent tables or columns.
2. Return the SQL query first, then on a new line write "-- Explanation:" followed by a brief explanation.
3. Use proper JOIN syntax when multiple tables are involved.
4. Use aliases for readability when joining tables.
5. If the requirement is ambiguous, make reasonable assumptions and note them.
6. Optimize the query for performance where possible.
7. Use the correct SQL dialect syntax for {dialect}."""

USER_PROMPT_TEMPLATE = """Database Schema:
{ddl_statements}

Requirement: {requirement}

Generate the SQL query:"""


def _column_to_ddl(column) -> str:
    parts = [f"    {column.name} {column.data_type}"]
    if column.is_primary_key:
        parts.append("PRIMARY KEY")
    if not column.is_nullable and not column.is_primary_key:
        parts.append("NOT NULL")
    if column.default_value is not None:
        parts.append(f"DEFAULT {column.default_value}")
    if column.foreign_key:
        ref_table, ref_col = column.foreign_key.rsplit(".", 1)
        parts.append(f"REFERENCES {ref_table}({ref_col})")
    return " ".join(parts)


def schema_to_ddl(schema: SchemaInput) -> str:
    ddl_statements = []
    for table in schema.tables:
        columns_ddl = ",\n".join(_column_to_ddl(col) for col in table.columns)
        ddl = f"CREATE TABLE {table.table_name} (\n{columns_ddl}\n);"
        ddl_statements.append(ddl)
    return "\n\n".join(ddl_statements)


def build_prompts(schema: SchemaInput, requirement: str) -> tuple[str, str]:
    dialect = schema.sql_dialect or "postgresql"
    ddl = schema_to_ddl(schema)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(dialect=dialect)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        ddl_statements=ddl, requirement=requirement
    )
    return system_prompt, user_prompt
