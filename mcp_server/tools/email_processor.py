"""Tool for processing and normalizing email addresses."""

import logging
import re
from typing import Any

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def normalize_email(email_address: str) -> dict[str, Any]:
    """
    Validate and normalize an email address based on common provider rules.

    Removes dots and sub-addressing (+) for Gmail/Google.
    Removes sub-addressing (+) for Outlook/Hotmail/Live.

    Args:
        email_address: The email address string to normalize.

    Returns:
        A dictionary containing:
            normalized_email: The normalized email string, or None if invalid.
            original_email: The original input email address.
            error: An error message string if validation or normalization failed, otherwise None.
    """
    original_email = email_address
    email = email_address.strip().lower()

    # Basic format validation
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        return {
            "normalized_email": None,
            "original_email": original_email,
            "error": "Invalid email format.",
        }

    # Additional structural checks before splitting
    try:
        local_part_for_check, domain_for_check = email.split("@", 1)
    except ValueError:
        # Should be caught by regex, but safeguard
        return {
            "normalized_email": None,
            "original_email": original_email,
            "error": "Invalid email structure (missing @).",
        }

    if (
        ".." in local_part_for_check
        or local_part_for_check.startswith(".")
        or local_part_for_check.endswith(".")
        or ".." in domain_for_check
        or domain_for_check.startswith(".")
        or domain_for_check.endswith(".")
        or "(" in email  # Parentheses are sometimes used for comments, invalid here
        or ")" in email
    ):
        return {
            "normalized_email": None,
            "original_email": original_email,
            "error": "Invalid email characters or structure.",
        }

    # Normalization logic
    try:
        local_part, domain = email.split("@", 1)  # Already validated that split works

        if domain in ["gmail.com", "googlemail.com", "google.com"]:
            local_part = local_part.replace(".", "")
            local_part = local_part.split("+", 1)[0]
        elif domain in ["outlook.com", "hotmail.com", "live.com"]:
            local_part = local_part.split("+", 1)[0]

        normalized_email = f"{local_part}@{domain}"

        return {
            "normalized_email": normalized_email,
            "original_email": original_email,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Error during email normalization: {e}", exc_info=True)
        return {
            "normalized_email": None,
            "original_email": original_email,
            "error": f"Internal server error during normalization: {str(e)}",
        }
