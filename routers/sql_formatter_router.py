import sqlparse
from fastapi import APIRouter, HTTPException, status

from models.sql_formatter_models import SqlFormatInput, SqlFormatOutput

router = APIRouter(prefix="/api/sql", tags=["SQL"])


@router.post("/format", response_model=SqlFormatOutput)
async def format_sql(payload: SqlFormatInput):
    """Format/prettify an SQL query string."""
    try:
        formatted = sqlparse.format(
            payload.sql_string,
            reindent=payload.reindent,
            keyword_case=payload.keyword_case,
            indent_width=payload.indent_width,
            # Other options can be added here
            # use_space_around_operators=True,
        )
        return {"formatted_sql": formatted}
    except Exception as e:
        print(f"Error formatting SQL: {e}")
        # sqlparse might not raise specific errors for bad SQL,
        # it might just format poorly or leave it as is.
        # We might want to just return the original or a generic error.
        # Let's raise 500 for now for unexpected issues.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during SQL formatting",
        )
