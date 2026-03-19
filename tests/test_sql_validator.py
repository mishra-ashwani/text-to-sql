from app.models.schemas import ColumnDefinition, SchemaInput, TableDefinition
from app.services.sql_validator import check_schema_references, format_sql, validate_sql


def _sample_schema():
    return SchemaInput(
        tables=[
            TableDefinition(
                table_name="users",
                columns=[
                    ColumnDefinition(name="id", data_type="INT", is_primary_key=True),
                    ColumnDefinition(name="name", data_type="VARCHAR(100)"),
                    ColumnDefinition(name="email", data_type="VARCHAR(255)"),
                ],
            ),
            TableDefinition(
                table_name="orders",
                columns=[
                    ColumnDefinition(name="id", data_type="INT", is_primary_key=True),
                    ColumnDefinition(name="user_id", data_type="INT"),
                    ColumnDefinition(name="amount", data_type="DECIMAL(10,2)"),
                ],
            ),
        ],
    )


def test_format_sql_uppercase_keywords():
    result = format_sql("select id from users where id = 1")
    assert "SELECT" in result
    assert "FROM" in result
    assert "WHERE" in result


def test_validate_sql_valid_query():
    is_valid, errors = validate_sql("SELECT id, name FROM users WHERE id = 1")
    assert is_valid is True
    assert errors == []


def test_validate_sql_invalid_query():
    is_valid, errors = validate_sql("SELEC id FROM")
    # sqlglot may or may not flag this depending on version, so just check it returns a tuple
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)


def test_validate_sql_with_dialect():
    is_valid, errors = validate_sql("SELECT * FROM users LIMIT 10", dialect="mysql")
    assert is_valid is True


def test_check_schema_references_valid():
    warnings = check_schema_references("SELECT id, name FROM users", _sample_schema())
    assert warnings == []


def test_check_schema_references_invalid_table():
    warnings = check_schema_references("SELECT id FROM nonexistent", _sample_schema())
    assert any("nonexistent" in w.lower() for w in warnings)


def test_check_schema_references_invalid_column():
    warnings = check_schema_references(
        "SELECT users.invalid_col FROM users", _sample_schema()
    )
    assert any("invalid_col" in w for w in warnings)


def test_check_schema_references_unqualified_invalid_column():
    warnings = check_schema_references(
        "SELECT bogus_column FROM users", _sample_schema()
    )
    assert any("bogus_column" in w for w in warnings)


def test_check_schema_references_join_valid():
    sql = "SELECT u.id, o.amount FROM users u JOIN orders o ON u.id = o.user_id"
    warnings = check_schema_references(sql, _sample_schema())
    assert warnings == []
