import json

from fastapi import APIRouter, HTTPException, status

from models.json_models import JsonFormatInput, JsonOutput, JsonTextInput

router = APIRouter(prefix="/api/json", tags=["JSON"])


@router.post("/format", response_model=JsonOutput)
async def format_json(payload: JsonFormatInput):
    """Format (pretty-print) a JSON string."""
    try:
        data = json.loads(payload.json_string)
        formatted_json = json.dumps(data, indent=payload.indent, sort_keys=payload.sort_keys, ensure_ascii=False)
        return {"result_string": formatted_json}
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON input: {e}")
    except Exception as e:
        print(f"Error formatting JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during JSON formatting",
        )


@router.post("/minify", response_model=JsonOutput)
async def minify_json(payload: JsonTextInput):
    """Minify a JSON string (remove unnecessary whitespace)."""
    try:
        data = json.loads(payload.json_string)
        minified_json = json.dumps(data, separators=(",", ":"), ensure_ascii=False)  # Most compact form
        return {"result_string": minified_json}
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON input: {e}")
    except Exception as e:
        print(f"Error minifying JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during JSON minification",
        )


# Could add a /validate endpoint too if needed
