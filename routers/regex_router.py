import re

from fastapi import APIRouter, HTTPException, status

from models.regex_models import RegexInput, RegexMatch, RegexOutput

router = APIRouter(prefix="/api/regex", tags=["Regex"])


@router.post("/test", response_model=RegexOutput)
async def test_regex(payload: RegexInput):
    """Test a regular expression against a string and return matches."""
    flags = 0
    if payload.ignore_case:
        flags |= re.IGNORECASE
    if payload.multiline:
        flags |= re.MULTILINE
    if payload.dot_all:
        flags |= re.DOTALL

    matches_list = []
    try:
        compiled_regex = re.compile(payload.regex_pattern, flags)

        for i, match in enumerate(compiled_regex.finditer(payload.test_string)):
            matches_list.append(
                RegexMatch(
                    match_index=i,
                    start=match.start(),
                    end=match.end(),
                    matched_string=match.group(0),
                    groups=list(match.groups()),
                    named_groups=match.groupdict(),
                )
            )

        return RegexOutput(matches=matches_list)

    except re.error as e:
        return RegexOutput(matches=[], error=f"Invalid regex pattern: {e}")
    except Exception as e:
        print(f"Error testing regex: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during regex testing",
        )
