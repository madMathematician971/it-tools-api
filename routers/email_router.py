import re

from fastapi import APIRouter, HTTPException, status

from models.email_models import EmailInput, EmailNormalizeOutput

router = APIRouter(prefix="/api/email", tags=["Email"])


@router.post("/normalize", response_model=EmailNormalizeOutput)
async def email_normalize(payload: EmailInput):
    """Normalize an email address based on common provider rules (e.g., Gmail)."""
    email = payload.email.strip().lower()

    # Use a more comprehensive regex for email validation (simplified RFC 5322)
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    if not re.match(email_regex, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format.")

    # Additional checks for common invalid patterns not caught by basic regex
    # Note: We don't check for '+.' here as it's handled by normalization rules
    local_part_for_check, domain_for_check = email.split("@", 1)
    if (
        ".." in local_part_for_check
        or local_part_for_check.startswith(".")
        or local_part_for_check.endswith(".")
        or ".." in domain_for_check
        or domain_for_check.startswith(".")
        or domain_for_check.endswith(".")
        or "(" in email
        or ")" in email
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email characters or structure.")

    try:
        local_part, domain = email.split("@", 1)

        if domain in ["gmail.com", "googlemail.com", "google.com"]:
            local_part = local_part.replace(".", "")
            local_part = local_part.split("+", 1)[0]
        elif domain in ["outlook.com", "hotmail.com", "live.com"]:
            local_part = local_part.split("+", 1)[0]

        normalized_email = f"{local_part}@{domain}"

        return {"normalized_email": normalized_email, "original_email": payload.email}
    except Exception as e:
        print(f"Error normalizing email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during email normalization",
        )
