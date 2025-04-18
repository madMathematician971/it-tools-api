"""
Tests for the Cron Parser tool.
"""

from datetime import datetime

import pytest

from mcp_server.tools.cron_parser import describe_cron, validate_cron

# Test cases for describe_cron: (input_cron, expected_description_part, expect_error)
TEST_CASES_DESCRIBE = [
    # 5-Field Standard
    ("*/5 * * * *", "Every 5 minutes", False),
    ("0 9 * * MON-FRI", "At 09:00 AM, Monday through Friday", False),
    ("0 0 1 JAN *", "At 12:00 AM, on day 1 of the month, only in January", False),
    ("5 4 * * sun", "At 04:05 AM, only on Sunday", False),
    # 6-Field Standard (with seconds) - Using actual cron-descriptor output
    ("0 * * * * *", "Every minute", False),
    ("*/10 * * * * *", "Every 10 seconds", False),
    # Error cases
    ("invalid cron string", "Invalid cron string", True),
    ("60 * * * *", "Invalid cron string", True),  # Invalid minute value (5-field)
    ("* 60 * * *", "Invalid cron string", True),  # Invalid hour value (5-field)
    # Updated expected error for 7 fields
    ("* * * * * * *", "Cron string must have 5 or 6 fields", True),
    ("-1 * * * * *", "Invalid cron string", True),  # Invalid second value (6-field)
]


@pytest.mark.parametrize("cron_string, description_part, expect_error", TEST_CASES_DESCRIBE)
def test_describe_cron(cron_string, description_part, expect_error):
    """Test describe_cron function."""
    result = describe_cron(cron_string=cron_string)

    if expect_error:
        assert result["error"] is not None
        assert description_part in result["error"]
        assert result["description"] is None
    else:
        assert result["error"] is None
        assert result["description"] is not None
        assert description_part in result["description"]


# Test cases for validate_cron: (input_cron, expect_valid, expect_runs, expect_error)
TEST_CASES_VALIDATE = [
    # 5-Field Standard
    ("*/1 * * * *", True, 5, False),  # Every minute
    ("0 12 1 * *", True, 5, False),  # 12:00 PM on the 1st of every month
    ("0 0 * * 0", True, 5, False),  # Midnight every Sunday
    # 6-Field Standard (with seconds)
    ("* * * * * *", True, 5, False),  # Every second
    ("0 0 12 * * *", True, 5, False),  # Every second during the 12:00 PM hour
    # Error cases
    ("invalid cron", False, 0, True),
    ("99 * * * *", False, 0, True),  # Invalid minute (5-field)
    ("99 * * * * *", False, 0, True),  # Invalid second (6-field)
    # Updated expected error for 7 fields
    ("* * * * * * *", False, 0, True),  # validate_cron should also reject 7 fields
]


@pytest.mark.parametrize("cron_string, expect_valid, runs_count, expect_error", TEST_CASES_VALIDATE)
def test_validate_cron(cron_string, expect_valid, runs_count, expect_error):
    """Test validate_cron function."""
    result = validate_cron(cron_string=cron_string)

    assert result["is_valid"] == expect_valid

    if expect_error:
        assert result["error"] is not None
        assert result["next_runs"] is None
    else:
        assert result["error"] is None
        if expect_valid:
            assert result["next_runs"] is not None
            assert isinstance(result["next_runs"], list)
            assert len(result["next_runs"]) == runs_count
            # Check if dates are valid ISO format strings
            for run_iso in result["next_runs"]:
                assert isinstance(run_iso, str)
                try:
                    datetime.fromisoformat(run_iso.replace("Z", "+00:00"))
                except ValueError:
                    pytest.fail(f"Invalid ISO format for next run time: {run_iso}")
        else:
            assert result["next_runs"] is None
