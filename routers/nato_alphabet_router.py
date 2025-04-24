import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.nato_converter import convert_from_nato, convert_to_nato
from models.nato_alphabet_models import NatoInput, NatoOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nato-alphabet", tags=["NATO Phonetic Alphabet"])


@router.post("/to-nato", response_model=NatoOutput)
async def convert_to_nato_router(input_data: NatoInput):
    """Convert text to NATO phonetic alphabet representation using the MCP tool."""
    try:
        # Call the MCP tool function
        result_dict = convert_to_nato(**input_data.model_dump())

        if result_dict["error"]:
            # Use the error from the tool for the HTTPException detail
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result_dict["error"])

        # Extract the successful result from the tool's output
        tool_result = result_dict["result"]
        if tool_result:
            return NatoOutput(
                input=input_data.text,  # Use original input text
                output=tool_result["output"],
                output_format=input_data.output_format.lower(),  # Use normalized format
                character_map=tool_result["character_map"],
            )
        else:
            logger.error("MCP convert_to_nato_tool returned no result and no error.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during NATO conversion.",
            )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error converting to NATO alphabet: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to convert to NATO alphabet: {str(e)}"
        )


@router.post(
    "/from-nato",
    # Change response model or how result is handled if needed, based on tool output
    response_model=NatoOutput,  # Change to NatoOutput
    summary="Convert NATO phonetic alphabet back to text using MCP tool",
)
async def nato_to_text(payload: NatoInput):  # Reuse NatoInput or create a specific DecodeInput
    """Converts a string of NATO phonetic words back to text using the MCP tool."""
    try:
        # Call the MCP tool function with specific arguments
        result_dict = convert_from_nato(nato_text=payload.text, separator=payload.separator)

        if result_dict["error"]:
            # Use the error from the tool
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result_dict["error"])

        # Return NatoOutput model
        return NatoOutput(
            input=payload.text,  # Original NATO text input
            output=result_dict["result"],  # Decoded text
            output_format="text",  # Fixed format for decode
            character_map={},  # No character map for reverse conversion
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error converting NATO alphabet to text: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during NATO-to-text conversion: {str(e)}",
        )
