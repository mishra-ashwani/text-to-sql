from typing import List, Tuple

import sqlglot
import sqlparse

from app.models.schemas import SchemaInput

DIALECT_MAP = {
    "postgresql": "postgres",
    "postgres": "postgres",
    "mysql": "mysql",
    "sqlite": "sqlite",
}


def format_sql(sql: str) -> str:
    return sqlparse.format(sql, reindent=True, keyword_case="upper")


def validate_sql(sql: str, dialect: str = "postgresql") -> Tuple[bool, List[str]]:
    errors = []
    mapped_dialect = DIALECT_MAP.get(dialect.lower(), dialect.lower())
    try:
        parsed = sqlglot.parse(sql, read=mapped_dialect)
        if not parsed:
            errors.append("Could not parse SQL")
    except sqlglot.errors.ParseError as e:
        errors.append(str(e))
    return (len(errors) == 0, errors)


def check_schema_references(sql: str, schema: SchemaInput) -> List[str]:
    """Check that tables referenced in the SQL exist in the provided schema."""
    warnings = []
    valid_tables = {t.table_name.lower() for t in schema.tables}

    try:
        parsed = sqlglot.parse(sql)
        for statement in parsed:
            if statement is None:
                continue
            for table in statement.find_all(sqlglot.exp.Table):
                table_name = table.name.lower()
                if table_name and table_name not in valid_tables:
                    warnings.append(
                        f"Table '{table.name}' is not defined in the provided schema"
                    )
    except Exception:
        pass

    return warnings
