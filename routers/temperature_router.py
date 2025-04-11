from fastapi import APIRouter, HTTPException, status

from models.temperature_models import (
    TemperatureInput,
    TemperatureOutput,
    TemperatureUnit,
)

router = APIRouter(prefix="/api/temperature", tags=["Temperature"])


@router.post("/convert", response_model=TemperatureOutput)
async def convert_temperature(payload: TemperatureInput):
    """Convert temperature between Celsius, Fahrenheit, and Kelvin."""
    c, f, k = None, None, None
    val = payload.value
    unit = payload.unit

    try:
        if unit == TemperatureUnit.celsius:
            c = val
            f = (c * 9 / 5) + 32
            k = c + 273.15
        elif unit == TemperatureUnit.fahrenheit:
            f = val
            c = (f - 32) * 5 / 9
            k = c + 273.15
        elif unit == TemperatureUnit.kelvin:
            k = val
            if k < 0:
                # Physical impossibility
                return TemperatureOutput(
                    celsius=0,
                    fahrenheit=0,
                    kelvin=k,
                    error="Kelvin cannot be below absolute zero (0 K).",
                )
            c = k - 273.15
            f = (c * 9 / 5) + 32
        else:
            # Should be caught by Pydantic
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid temperature unit specified.",
            )

        # Round results for cleaner output (e.g., 2 decimal places)
        return TemperatureOutput(celsius=round(c, 2), fahrenheit=round(f, 2), kelvin=round(k, 2))

    except Exception as e:
        print(f"Error converting temperature: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during temperature conversion",
        )
