from app.services.llm_service import LLMService


def test_clean_response_strips_code_fences():
    assert LLMService._clean_response("```sql\nSELECT 1;\n```") == "SELECT 1;"


def test_clean_response_strips_plain_fences():
    assert LLMService._clean_response("```\nSELECT 1;\n```") == "SELECT 1;"


def test_clean_response_no_fences():
    assert LLMService._clean_response("  SELECT 1;  ") == "SELECT 1;"


def test_looks_like_sql_select():
    assert LLMService._looks_like_sql("SELECT id FROM users") is True


def test_looks_like_sql_insert():
    assert LLMService._looks_like_sql("INSERT INTO users VALUES (1)") is True


def test_looks_like_sql_negative():
    assert LLMService._looks_like_sql("Here is a plain text explanation") is False


def test_looks_like_sql_with_cte():
    assert LLMService._looks_like_sql("WITH cte AS (SELECT 1) SELECT * FROM cte") is True
