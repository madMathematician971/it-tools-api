"""
Hash calculator tool for MCP server.
"""

import hashlib

from mcp_server import mcp_app


@mcp_app.tool()
def calculate_hash(text: str) -> dict:
    """
    Calculate various hash digests (MD5, SHA1, SHA256, SHA512) for the input text.

    Args:
        text: The text to hash

    Returns:
        A dictionary containing the digests for MD5, SHA1, SHA256, and SHA512
    """
    try:
        text_bytes = text.encode("utf-8")

        md5_hash = hashlib.md5(text_bytes).hexdigest()
        sha1_hash = hashlib.sha1(text_bytes).hexdigest()
        sha256_hash = hashlib.sha256(text_bytes).hexdigest()
        sha512_hash = hashlib.sha512(text_bytes).hexdigest()

        return {
            "md5": md5_hash,
            "sha1": sha1_hash,
            "sha256": sha256_hash,
            "sha512": sha512_hash,
        }
    except Exception as e:
        raise ValueError(f"Error calculating hashes: {e}")
