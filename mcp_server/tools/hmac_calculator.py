"""
HMAC calculator tool for MCP server.
"""

import hashlib
import hmac

from mcp_server import mcp_app

# Map algorithm names to hashlib functions
HASH_ALGOS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}


@mcp_app.tool()
def calculate_hmac(text: str, key: str, algorithm: str = "sha256") -> dict:
    """
    Calculate HMAC digest for input text using a secret key and hash algorithm.

    Args:
        text: The text to calculate HMAC for
        key: The secret key
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)

    Returns:
        A dictionary containing the HMAC digest in hexadecimal
    """
    # Validate algorithm
    algo_name = algorithm.lower()
    if algo_name not in HASH_ALGOS:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {list(HASH_ALGOS.keys())}")

    try:
        # Calculate HMAC
        text_bytes = text.encode("utf-8")
        key_bytes = key.encode("utf-8")
        hash_func = HASH_ALGOS[algo_name]

        hmac_digest = hmac.new(key_bytes, text_bytes, hash_func).hexdigest()

        return {"hmac_hex": hmac_digest, "algorithm": algorithm}
    except Exception as e:
        raise ValueError(f"Error calculating HMAC: {e}")
