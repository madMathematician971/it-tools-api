import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.regex_models import RegexInput, RegexMatch, RegexOutput
from routers.regex_router import router as regex_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(regex_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Regex Matching ---


@pytest.mark.parametrize(
    "regex_pattern, test_string, ignore_case, multiline, dot_all, expected_matches",
    [
        # Simple match
        (
            r"hello",
            "hello world",
            False,
            False,
            False,
            [RegexMatch(match_index=0, start=0, end=5, matched_string="hello", groups=[], named_groups={})],
        ),
        # No match
        (r"goodbye", "hello world", False, False, False, []),
        # Multiple matches
        (
            r"\d+",
            "Numbers: 123, 45, 6789",
            False,
            False,
            False,
            [
                RegexMatch(match_index=0, start=9, end=12, matched_string="123", groups=[], named_groups={}),
                RegexMatch(match_index=1, start=14, end=16, matched_string="45", groups=[], named_groups={}),
                RegexMatch(match_index=2, start=18, end=22, matched_string="6789", groups=[], named_groups={}),
            ],
        ),
        # Ignore case
        (
            r"apple",
            "An Apple a day",
            True,
            False,
            False,
            [RegexMatch(match_index=0, start=3, end=8, matched_string="Apple", groups=[], named_groups={})],
        ),
        (
            r"apple",
            "An APPLE a day",
            True,
            False,
            False,
            [RegexMatch(match_index=0, start=3, end=8, matched_string="APPLE", groups=[], named_groups={})],
        ),
        # Multiline
        (
            r"^start",
            "line1\nstart line2",
            False,
            True,
            False,
            [RegexMatch(match_index=0, start=6, end=11, matched_string="start", groups=[], named_groups={})],
        ),
        (
            r"end$",
            "line1 end\nline2",
            False,
            True,
            False,
            [RegexMatch(match_index=0, start=6, end=9, matched_string="end", groups=[], named_groups={})],
        ),
        # Dot All
        (
            r"begin.*end",
            "begin\nmiddle\nend",
            False,
            False,
            True,
            [
                RegexMatch(
                    match_index=0, start=0, end=16, matched_string="begin\nmiddle\nend", groups=[], named_groups={}
                )
            ],
        ),
        # Groups
        (
            r"(\w+) (\w+)",
            "John Doe",
            False,
            False,
            False,
            [
                RegexMatch(
                    match_index=0, start=0, end=8, matched_string="John Doe", groups=["John", "Doe"], named_groups={}
                )
            ],
        ),
        # Named Groups
        (
            r"(?P<first>\w+) (?P<last>\w+)",
            "Jane Smith",
            False,
            False,
            False,
            [
                RegexMatch(
                    match_index=0,
                    start=0,
                    end=10,
                    matched_string="Jane Smith",
                    groups=["Jane", "Smith"],
                    named_groups={"first": "Jane", "last": "Smith"},
                )
            ],
        ),
        # Empty string/pattern
        (
            r"",
            "abc",
            False,
            False,
            False,
            [  # Matches empty string at each position
                RegexMatch(match_index=0, start=0, end=0, matched_string="", groups=[], named_groups={}),
                RegexMatch(match_index=1, start=1, end=1, matched_string="", groups=[], named_groups={}),
                RegexMatch(match_index=2, start=2, end=2, matched_string="", groups=[], named_groups={}),
                RegexMatch(match_index=3, start=3, end=3, matched_string="", groups=[], named_groups={}),
            ],
        ),
        (r"abc", "", False, False, False, []),  # No match in empty string
    ],
)
@pytest.mark.asyncio
async def test_regex_success(
    client: TestClient,
    regex_pattern: str,
    test_string: str,
    ignore_case: bool,
    multiline: bool,
    dot_all: bool,
    expected_matches: list[RegexMatch],
):
    """Test successful regex matching with various patterns and flags."""
    payload = RegexInput(
        regex_pattern=regex_pattern,
        test_string=test_string,
        ignore_case=ignore_case,
        multiline=multiline,
        dot_all=dot_all,
    )
    response = client.post("/api/regex/test", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = RegexOutput(**response.json())

    assert output.error is None
    assert len(output.matches) == len(expected_matches)
    # Convert output matches to dicts for easier comparison if needed, or compare fields directly
    for i, match in enumerate(output.matches):
        expected = expected_matches[i]
        assert match.match_index == expected.match_index
        assert match.start == expected.start
        assert match.end == expected.end
        assert match.matched_string == expected.matched_string
        assert match.groups == expected.groups
        assert match.named_groups == expected.named_groups


@pytest.mark.parametrize(
    "invalid_pattern, error_substring",
    [
        (r"([a-z)", "unterminated character set"),  # Updated from "unbalanced parenthesis"
        (r"*abc", "nothing to repeat"),
        (r"[a-z", "unterminated character set"),
    ],
)
@pytest.mark.asyncio
async def test_regex_invalid_pattern(client: TestClient, invalid_pattern: str, error_substring: str):
    """Test regex matching with invalid patterns."""
    payload = RegexInput(
        regex_pattern=invalid_pattern,
        test_string="some text",
        ignore_case=False,
        multiline=False,
        dot_all=False,
    )
    response = client.post("/api/regex/test", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK  # API returns 200 OK with error
    output = RegexOutput(**response.json())
    assert output.error is not None
    assert "Invalid regex pattern" in output.error
    # Check for the specific error detail (case-insensitive)
    assert error_substring.lower() in output.error.lower()
