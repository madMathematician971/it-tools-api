"""
UUID generator tool for MCP server.
"""

import uuid

from mcp_server import mcp_app


@mcp_app.tool()
def generate_uuid(version: int = 4, namespace: str | None = None, name: str | None = None) -> dict:
    """
    Generate a UUID of the specified version.

    Args:
        version: UUID version (1, 3, 4, or 5)
        namespace: Namespace UUID (only for version 3 or 5)
        name: Name within namespace (only for version 3 or 5)

    Returns:
        A dictionary containing:
            uuid: The generated UUID string
            version: UUID version (1, 4, etc.)
            variant: UUID variant
            is_nil: Whether the UUID is nil (all zeros)
            hex: Hexadecimal representation (no dashes)
            bytes: Bytes representation (as hex)
            urn: URN representation
            integer: Integer representation
            binary: Binary representation
    """
    if version not in [1, 3, 4, 5]:
        raise ValueError(f"Unsupported UUID version: {version}. Must be 1, 3, 4, or 5.")

    uuid_obj = None

    if version == 1:
        # Time-based UUID
        uuid_obj = uuid.uuid1()
    elif version == 3:
        # Name-based UUID with MD5
        if not namespace or not name:
            raise ValueError("For UUID version 3, both namespace and name must be provided")
        try:
            namespace_uuid = uuid.UUID(namespace)
        except ValueError:
            raise ValueError(f"Invalid namespace UUID: {namespace}")
        uuid_obj = uuid.uuid3(namespace_uuid, name)
    elif version == 4:
        # Random UUID
        uuid_obj = uuid.uuid4()
    elif version == 5:
        # Name-based UUID with SHA-1
        if not namespace or not name:
            raise ValueError("For UUID version 5, both namespace and name must be provided")
        try:
            namespace_uuid = uuid.UUID(namespace)
        except ValueError:
            raise ValueError(f"Invalid namespace UUID: {namespace}")
        uuid_obj = uuid.uuid5(namespace_uuid, name)

    # Assert version is not None (should be guaranteed for v1/v4)
    assert uuid_obj.version is not None, "Generated UUID has no version"

    # Variant name mapping
    variant_names = {
        uuid.RFC_4122: "RFC 4122",
        uuid.RESERVED_NCS: "NCS (Reserved)",
        uuid.RESERVED_MICROSOFT: "Microsoft (Reserved)",
        uuid.RESERVED_FUTURE: "Future (Reserved)",
    }

    # Format as binary string (128 bits)
    binary = format(int(uuid_obj), "0128b")

    # Create response
    return {
        "uuid": str(uuid_obj),
        "version": uuid_obj.version,
        "variant": variant_names.get(uuid_obj.variant, "Unknown"),
        "is_nil": uuid_obj == uuid.UUID(int=0),
        "hex": uuid_obj.hex,
        "bytes": uuid_obj.bytes.hex(),
        "urn": uuid_obj.urn,
        "integer": uuid_obj.int,
        "binary": binary,
    }
