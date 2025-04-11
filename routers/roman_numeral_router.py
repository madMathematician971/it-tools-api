import logging

from fastapi import APIRouter

from models.roman_numeral_models import RomanDecodeInput, RomanEncodeInput, RomanOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roman-numerals", tags=["Roman Numeral Converter"])

# Roman numeral mapping (descending order for easy conversion)
ROMAN_MAP = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]

# Reverse mapping for decoding
DECIMAL_MAP = {v: k for k, v in ROMAN_MAP}


@router.post("/encode", response_model=RomanOutput)
async def encode_to_roman(input_data: RomanEncodeInput):
    """Convert an integer (1-3999) to its Roman numeral representation."""
    try:
        number = input_data.number
        result = ""
        for value, numeral in ROMAN_MAP:
            while number >= value:
                result += numeral
                number -= value

        return RomanOutput(input_value=input_data.number, result=result)

    except Exception as e:
        logger.error(f"Error encoding to Roman numeral: {e}", exc_info=True)
        return RomanOutput(input_value=input_data.number, result="", error=f"Failed to encode: {str(e)}")


@router.post("/decode", response_model=RomanOutput)
async def decode_from_roman(input_data: RomanDecodeInput):
    """Convert a Roman numeral string to its integer representation."""
    try:
        roman_numeral = input_data.roman_numeral.upper()
        result = 0
        i = 0
        while i < len(roman_numeral):
            # Check for two-character subtractive combinations (e.g., CM, IX)
            if i + 1 < len(roman_numeral) and roman_numeral[i : i + 2] in DECIMAL_MAP:
                result += DECIMAL_MAP[roman_numeral[i : i + 2]]
                i += 2
            # Otherwise, process single character
            elif roman_numeral[i] in DECIMAL_MAP:
                result += DECIMAL_MAP[roman_numeral[i]]
                i += 1
            else:
                # Should be caught by validator, but good to have a fallback
                raise ValueError(f"Invalid Roman numeral symbol: {roman_numeral[i]}")

        # Basic check for validity (e.g., converted value should re-encode to original)
        # This helps catch some invalid inputs like 'IIII' or 'VV'
        re_encoded = await encode_to_roman(RomanEncodeInput(number=result))
        if re_encoded.result != roman_numeral:
            raise ValueError("Roman numeral is not in standard form.")

        return RomanOutput(input_value=input_data.roman_numeral, result=result)

    except ValueError as ve:
        return RomanOutput(input_value=input_data.roman_numeral, result=0, error=f"Invalid Roman numeral: {str(ve)}")
    except Exception as e:
        logger.error(f"Error decoding Roman numeral: {e}", exc_info=True)
        return RomanOutput(input_value=input_data.roman_numeral, result=0, error=f"Failed to decode: {str(e)}")
