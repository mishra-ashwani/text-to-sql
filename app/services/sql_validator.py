import logging
from typing import List, Tuple

import sqlglot
import sqlparse

from app.models.schemas import SchemaInput

logger = logging.getLogger(__name__)

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
    """Check that tables and columns referenced in the SQL exist in the provided schema."""
    warnings = []
    valid_tables = {t.table_name.lower() for t in schema.tables}
    valid_columns: dict[str, set[str]] = {}
    for t in schema.tables:
        valid_columns[t.table_name.lower()] = {c.name.lower() for c in t.columns}

    all_columns = set()
    for cols in valid_columns.values():
        all_columns.update(cols)

    try:
        parsed = sqlglot.parse(sql)
        for statement in parsed:
            if statement is None:
                continue

            # Check tables
            for table in statement.find_all(sqlglot.exp.Table):
                table_name = table.name.lower()
                if table_name and table_name not in valid_tables:
                    warnings.append(
                        f"Table '{table.name}' is not defined in the provided schema"
                    )

            # Check columns
            for column in statement.find_all(sqlglot.exp.Column):
                col_name = column.name.lower()
                table_ref = column.table.lower() if column.table else ""

                if table_ref and table_ref in valid_tables:
                    if col_name not in valid_columns[table_ref]:
                        warnings.append(
                            f"Column '{column.name}' is not defined in table '{table_ref}'"
                        )
                elif not table_ref and col_name not in all_columns:
                    warnings.append(
                        f"Column '{column.name}' is not defined in any table in the schema"
                    )
    except sqlglot.errors.ParseError as e:
        logger.warning("Failed to parse SQL for schema reference check: %s", e)

    return warnings
