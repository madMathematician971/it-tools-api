import logging
import math
import time

from fastapi import APIRouter, HTTPException, status
from zxcvbn import zxcvbn

from models.password_strength_models import (
    CrackTimeDisplay,
    CrackTimeSeconds,
    Feedback,
    PasswordInput,
    PasswordStrengthOutput,
    SequenceItem,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/password-strength", tags=["Password Strength Analyzer"])


@router.post("/check", response_model=PasswordStrengthOutput)
async def check_password_strength(input_data: PasswordInput):
    """Check strength of a password using zxcvbn."""
    password = input_data.password.strip()

    if not password:
        logger.warning("Empty password submitted")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password cannot be empty")

    try:
        start_time = time.time_ns()
        result = zxcvbn(password)
        calc_time = time.time_ns() - start_time

        # Process matches for additional details
        matches = []
        for match in result.get("sequence", []):
            match_dict = vars(match) if hasattr(match, "__dict__") else match
            seq_item = SequenceItem(
                pattern=match_dict.get("pattern", ""),
                pattern_name=match_dict.get("pattern_name", ""),
                token=match_dict.get("token", ""),
                token_start_index=match_dict.get("i", 0),
                token_end_index=match_dict.get("j", 0),
                i=match_dict.get("i", 0),
                j=match_dict.get("j", 0),
                sub_display=match_dict.get("sub_display", ""),
                base_entropy_per_char=match_dict.get("base_entropy_per_char", 0.0),
                entropy_per_char=match_dict.get("entropy_per_char", 0.0),
                repeat_count=match_dict.get("repeat_count", 1),
                base_token=match_dict.get("base_token", ""),
                token_entropy=match_dict.get("token_entropy", 0.0),
                match_entropy=match_dict.get("entropy", 0.0),
            )
            matches.append(seq_item)

        # Map score to descriptive strength rating
        score = result.get("score", 0)
        strength_map = {
            0: "Very Weak",
            1: "Weak",
            2: "Fair",
            3: "Good",
            4: "Strong",
        }
        strength = strength_map.get(score, "Unknown")

        # Extract crack times
        crack_times_seconds = result.get("crack_times_seconds", {})
        crack_times_display = result.get("crack_times_display", {})

        # Build feedback object
        feedback_data = result.get("feedback", {})
        warning = feedback_data.get("warning", None)
        suggestions = feedback_data.get("suggestions", [])

        return PasswordStrengthOutput(
            password=password,
            entropy=result.get("guesses_log10", 0) * math.log(10),  # Convert log10 to natural log for entropy
            crack_time_seconds=CrackTimeSeconds(
                offline_fast_hashing_1e10_per_second=crack_times_seconds.get("offline_fast_hashing_1e10_per_second", 0),
                offline_slow_hashing_1e4_per_second=crack_times_seconds.get("offline_slow_hashing_1e4_per_second", 0),
                online_no_throttling_10_per_second=crack_times_seconds.get("online_no_throttling_10_per_second", 0),
                online_throttling_100_per_hour=crack_times_seconds.get("online_throttling_100_per_hour", 0),
            ),
            crack_time_display=CrackTimeDisplay(
                offline_fast_hashing_1e10_per_second=crack_times_display.get(
                    "offline_fast_hashing_1e10_per_second", ""
                ),
                offline_slow_hashing_1e4_per_second=crack_times_display.get("offline_slow_hashing_1e4_per_second", ""),
                online_no_throttling_10_per_second=crack_times_display.get("online_no_throttling_10_per_second", ""),
                online_throttling_100_per_hour=crack_times_display.get("online_throttling_100_per_hour", ""),
            ),
            score=score,
            feedback=Feedback(warning=warning, suggestions=suggestions),
            calc_time=calc_time // 1000000,  # Convert ns to ms
            matches=matches,
            strength=strength,
        )
    except Exception as e:
        logger.error(f"Error analyzing password strength: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze password: {str(e)}",
        )
