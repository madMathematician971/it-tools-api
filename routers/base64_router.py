import base64
import io
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from mcp_server.tools import base64_decode_string, base64_encode_string
from models.base64_models import Base64DecodeFileRequest, InputString, OutputString

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/base64", tags=["Base64"])


@router.post("/encode", response_model=OutputString)
async def base64_encode(payload: InputString):
    """Encode a string to Base64."""
    try:
        return {"result": base64_encode_string(payload.input)["result_string"]}
    except Exception as e:
        print(f"Error encoding Base64: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during encoding",
        )


@router.post("/decode", response_model=OutputString)
async def base64_decode(payload: InputString):
    """Decode a Base64 string."""
    try:
        result_dict = base64_decode_string(payload.input)
        if result_dict["error"]:
            logger.warning(f"Invalid Base64 input provided: {result_dict['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Base64 input string: {result_dict['error']}",
            )
        return {"result": result_dict["result_string"]}
    except HTTPException:  # Re-raise HTTPException if already raised
        raise
    except Exception as e:
        logger.error(f"Error decoding Base64: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during decoding",
        )


@router.post(
    "/encode-file",
    response_model=OutputString,
    summary="Encode a file to Base64 string",
)
async def base64_encode_file(file: UploadFile = File(...)):
    """Encode an uploaded file content to a Base64 string."""
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        encoded_bytes = base64.b64encode(contents)
        return OutputString(result=encoded_bytes.decode("utf-8"))
    except Exception as e:
        logger.error(f"Error encoding file to Base64: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during file encoding: {str(e)}",
        )
    finally:
        await file.close()


@router.post(
    "/decode-file",
    response_class=StreamingResponse,
    summary="Decode a Base64 string to a file",
)
async def base64_decode_file(payload: Base64DecodeFileRequest):
    """Decode a Base64 string and return it as a file download."""
    try:
        input_bytes = payload.base64_string.encode("utf-8")
        missing_padding = len(input_bytes) % 4
        if missing_padding:
            input_bytes += b"=" * (4 - missing_padding)

        decoded_bytes = base64.b64decode(input_bytes, validate=True)

        file_stream = io.BytesIO(decoded_bytes)

        # Sanitize filename - basic example, consider more robust sanitization
        safe_filename = "".join(c for c in payload.filename if c.isalnum() or c in (".", "-", "_"))
        if not safe_filename:
            safe_filename = "decoded_file"

        headers = {"Content-Disposition": f'attachment; filename="{safe_filename}"'}

        return StreamingResponse(file_stream, media_type="application/octet-stream", headers=headers)

    except (base64.binascii.Error, UnicodeDecodeError) as e:
        logger.error(f"Error decoding Base64 string for file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Base64 input string: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error decoding Base64 to file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during file decoding: {str(e)}",
        )
