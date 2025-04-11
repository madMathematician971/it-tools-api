import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from models.uuid_models import UuidResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/uuid", tags=["UUID Generator"])


class UuidInput(BaseModel):
    namespace: Optional[str] = Field(None, description="Namespace UUID for V3/V5 generation")
    name: Optional[str] = Field(None, description="Name string for V3/V5 generation")


class UuidOutput(BaseModel):
    version: int
    uuid_str: str = Field(..., alias="uuid")


@router.get("/", response_model=UuidResponse)
async def get_uuid_details(version: int = Query(4, description="UUID version to generate (1 or 4)", ge=1, le=4)):
    """Generate a UUID of the specified version with detailed info."""
    # Validate version
    if version not in [1, 4]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported UUID version: {version}. Only versions 1 and 4 are supported.",
        )

    # Generate UUID based on validated version
    if version == 1:
        generated_uuid = uuid.uuid1()
    else:  # version == 4
        generated_uuid = uuid.uuid4()

    # Assert version is not None (should be guaranteed for v1/v4)
    assert generated_uuid.version is not None, "Generated UUID has no version"

    # Variant name mapping
    variant_names = {
        uuid.RFC_4122: "RFC 4122",
        uuid.RESERVED_NCS: "NCS (Reserved)",
        uuid.RESERVED_MICROSOFT: "Microsoft (Reserved)",
        uuid.RESERVED_FUTURE: "Future (Reserved)",
    }

    # Format as binary string (128 bits)
    binary = format(int(generated_uuid), "0128b")

    # Create response
    return UuidResponse(
        uuid=str(generated_uuid),
        version=generated_uuid.version,
        variant=variant_names.get(generated_uuid.variant, "Unknown"),
        is_nil=generated_uuid == uuid.UUID(int=0),
        hex=generated_uuid.hex,
        bytes=generated_uuid.bytes.hex(),
        urn=generated_uuid.urn,
        integer=generated_uuid.int,
        binary=binary,
    )


@router.post("/v{version}", response_model=UuidOutput)
async def generate_uuid(version: int = Path(..., ge=1, le=5), payload: Optional[UuidInput] = None):
    """Generate a UUID of the specified version."""
    try:
        if version == 1:
            gen_uuid = uuid.uuid1()
        elif version == 3:
            if not payload or not payload.namespace or not payload.name:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Namespace and name required for UUIDv3")
            ns_uuid = uuid.UUID(payload.namespace)
            gen_uuid = uuid.uuid3(ns_uuid, payload.name)
        elif version == 4:
            gen_uuid = uuid.uuid4()
        elif version == 5:
            if not payload or not payload.namespace or not payload.name:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Namespace and name required for UUIDv5")
            ns_uuid = uuid.UUID(payload.namespace)
            gen_uuid = uuid.uuid5(ns_uuid, payload.name)
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid UUID version: {version}")

        return UuidOutput(version=version, uuid_str=str(gen_uuid))

    except ValueError as e:
        logger.warning(f"Invalid input for UUID generation (v{version}): {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid input: {e}")
    except Exception as e:
        logger.error(f"Error generating UUID (v{version}): {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error generating UUID")
