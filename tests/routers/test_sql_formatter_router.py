import pytest
import sqlparse  # For comparison
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.sql_formatter_models import SqlFormatOutput
from routers.sql_formatter_router import router as sql_formatter_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(sql_formatter_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test SQL Formatting ---

# Sample SQL strings
UNFORMATTED_SQL = "SELECT col1, col2 FROM my_table WHERE id=1;"
FORMATTED_SQL_DEFAULT = sqlparse.format(UNFORMATTED_SQL, reindent=True, keyword_case="lower", indent_width=2)
FORMATTED_SQL_UPPER = sqlparse.format(UNFORMATTED_SQL, reindent=True, keyword_case="upper", indent_width=2)
FORMATTED_SQL_INDENT4 = sqlparse.format(UNFORMATTED_SQL, reindent=True, keyword_case="lower", indent_width=4)
FORMATTED_SQL_NOREINDENT = sqlparse.format(UNFORMATTED_SQL, reindent=False, keyword_case="lower", indent_width=2)


@pytest.mark.parametrize(
    "input_sql, reindent, keyword_case, indent_width, expected_sql",
    [
        (UNFORMATTED_SQL, True, "lower", 2, FORMATTED_SQL_DEFAULT),
        (UNFORMATTED_SQL, True, "upper", 2, FORMATTED_SQL_UPPER),
        (UNFORMATTED_SQL, True, "lower", 4, FORMATTED_SQL_INDENT4),
        (UNFORMATTED_SQL, False, "lower", 2, FORMATTED_SQL_NOREINDENT),
        # Test with already formatted SQL
        (FORMATTED_SQL_DEFAULT, True, "lower", 2, FORMATTED_SQL_DEFAULT),
        # Test with more complex query
        (
            "select a,b,c from table1 join table2 on table1.id=table2.fk where table1.col > 10 order by a desc;",
            True,
            "lower",
            2,
            sqlparse.format(
                "select a,b,c from table1 join table2 on table1.id=table2.fk where table1.col > 10 order by a desc;",
                reindent=True,
                keyword_case="lower",
                indent_width=2,
            ),
        ),
        # Test with syntax that might be tricky (comments, etc.) - sqlparse handles many cases
        (
            "SELECT --comment\n col FROM tbl;",
            True,
            "lower",
            2,
            sqlparse.format("SELECT --comment\n col FROM tbl;", reindent=True, keyword_case="lower", indent_width=2),
        ),
        # Empty input
        ("", True, "lower", 2, ""),
    ],
)
@pytest.mark.asyncio
async def test_format_sql_success(
    client: TestClient, input_sql: str, reindent: bool, keyword_case: str, indent_width: int, expected_sql: str
):
    """Test successful SQL formatting with various options."""
    payload_dict = {
        "sql_string": input_sql,
        "reindent": reindent,
        "keyword_case": keyword_case,
        "indent_width": indent_width,
    }
    response = client.post("/api/sql/format", json=payload_dict)

    assert response.status_code == status.HTTP_200_OK
    output = SqlFormatOutput(**response.json())
    # Compare the formatted output directly
    assert output.formatted_sql.strip() == expected_sql.strip()


# Test for potentially invalid input types (should be caught by Pydantic)
@pytest.mark.asyncio
async def test_format_sql_invalid_type(client: TestClient):
    """Test providing invalid types for formatting options."""
    response = client.post(
        "/api/sql/format",
        json={
            "sql_string": "SELECT 1;",
            "reindent": "not-a-bool",
            "keyword_case": "mixed",  # Invalid enum value
            "indent_width": -1,  # Invalid value
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check for part of the specific Pydantic validation error message
    assert "input should be" in response.text.lower()
