import logging
import random
import socket
from typing import List, Set

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from models.random_port_models import PortResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/random-port", tags=["Random Port Generator"])

# Standard port ranges
MIN_PORT = 1
MAX_PORT = 65535
WELL_KNOWN_PORTS_MAX = 1023
REGISTERED_PORTS_MAX = 49151
# Simple list of common ports to potentially exclude (expand as needed)
COMMON_PORTS_TO_EXCLUDE: Set[int] = {
    20,
    21,
    22,
    23,
    25,
    53,
    80,
    110,
    143,
    443,
    465,
    587,
    993,
    995,  # Common services
    3306,
    5432,
    1433,
    1521,  # Databases
    27017,  # MongoDB
    6379,  # Redis
    11211,  # Memcached
    8080,
    8000,  # Common alt HTTP
}

# Port Ranges Definition
WELL_KNOWN_PORTS = (0, 1023)
REGISTERED_PORTS = (1024, 49151)
EPHEMERAL_PORTS = (49152, 65535)


# Response model for returning a list of ports
class PortListResponse(BaseModel):
    ports: List[int] = Field(..., description="A list of generated random ports.")


@router.get("/", response_model=PortResponse)
async def generate_random_port(
    port_type: str = Query(
        "any",
        description="Type of port to generate: 'well-known', 'registered', 'ephemeral', or 'any'.",
        pattern=r"^(well-known|registered|ephemeral|any)$",
    ),
    protocol: str = Query(
        "tcp", description="Protocol to check service name for (tcp or udp).", pattern=r"^(tcp|udp)$"
    ),
):
    """Generate a random network port number, optionally within a specific range."""
    try:
        port_type = port_type.lower()
        protocol = protocol.lower()

        if port_type == "well-known":
            min_port, max_port = WELL_KNOWN_PORTS
            range_type_str = "Well-Known"
        elif port_type == "registered":
            min_port, max_port = REGISTERED_PORTS
            range_type_str = "Registered"
        elif port_type == "ephemeral":
            min_port, max_port = EPHEMERAL_PORTS
            range_type_str = "Ephemeral (Dynamic/Private)"
        elif port_type == "any":
            min_port, max_port = 0, 65535
            range_type_str = "Any"
        else:
            # Should be caught by regex, but safeguard
            raise ValueError("Invalid port type specified")

        # Generate random port within the selected range
        random_port = random.randint(min_port, max_port)

        # Determine range type for output if 'any' was chosen initially
        if range_type_str == "Any":
            if WELL_KNOWN_PORTS[0] <= random_port <= WELL_KNOWN_PORTS[1]:
                range_type_str = "Well-Known"
            elif REGISTERED_PORTS[0] <= random_port <= REGISTERED_PORTS[1]:
                range_type_str = "Registered"
            else:
                range_type_str = "Ephemeral (Dynamic/Private)"

        # Try to get common service name
        service_name = None
        try:
            service_name = socket.getservbyport(random_port, protocol)
        except OSError:
            pass  # Port not assigned a common service name for the protocol

        return PortResponse(port=random_port, range_type=range_type_str, service_name=service_name)

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error generating random port: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate random port: {str(e)}",
        )


@router.get("/generate", response_model=PortListResponse, summary="Generate random network ports")
async def generate_random_ports(
    count: int = Query(1, description="Number of random ports to generate.", ge=1, le=100),
    min_port: int = Query(
        MIN_PORT,
        description="Minimum port number (inclusive).",
        ge=MIN_PORT,
        le=MAX_PORT,
    ),
    max_port: int = Query(
        MAX_PORT,
        description="Maximum port number (inclusive).",
        ge=MIN_PORT,
        le=MAX_PORT,
    ),
    exclude_well_known: bool = Query(False, description="Exclude ports 1-1023 (requires min_port > 1023)."),
    exclude_common: bool = Query(False, description="Exclude a predefined list of common service ports."),
):
    """
    Generates one or more random network ports within a specified range,
    with options to exclude well-known or common ports.

    - **count**: Number of ports to generate.
    - **min_port**: Minimum port number.
    - **max_port**: Maximum port number.
    - **exclude_well_known**: If true, ensures generated ports are > 1023.
    - **exclude_common**: If true, attempts to exclude ports from a predefined common list.
    """
    if min_port > max_port:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum port cannot be greater than maximum port.",
        )

    actual_min = min_port
    if exclude_well_known:
        if actual_min <= WELL_KNOWN_PORTS_MAX:
            actual_min = WELL_KNOWN_PORTS_MAX + 1
        if actual_min > max_port:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot exclude well-known ports because the specified range is entirely within the well-known range.",
            )

    # Calculate the size of the valid range
    available_range_size = max_port - actual_min + 1
    exclusions: Set[int] = set()
    if exclude_common:
        exclusions = {p for p in COMMON_PORTS_TO_EXCLUDE if actual_min <= p <= max_port}
        available_range_size -= len(exclusions)

    if available_range_size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The specified range and exclusions result in no available ports.",
        )
    if count > available_range_size:
        logger.warning(
            f"Requested count ({count}) is larger than available unique ports ({available_range_size}) in the range/exclusions. Returning duplicates."
        )
        # Allow duplicates in this case, maybe return error?
        # For now, just generate with replacement if count is too high

    generated_ports = []
    attempts = 0
    max_attempts = count * 5 + 100  # Safety break for tight ranges/exclusions

    try:
        # If count is small relative to range, random.randint is fine
        # If count is large, generating all possibilities and sampling might be better, but more complex
        while len(generated_ports) < count and attempts < max_attempts:
            attempts += 1
            port = random.randint(actual_min, max_port)
            if exclude_common and port in exclusions:
                continue
            generated_ports.append(port)

        if len(generated_ports) < count:
            logger.warning(
                f"Could only generate {len(generated_ports)} unique ports out of {count} requested after {max_attempts} attempts."
            )
            # Decide: return partial list or raise error? Returning partial for now.
            if not generated_ports:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate any ports within the constraints.",
                )

        return PortListResponse(ports=generated_ports)

    except Exception as e:
        logger.error(f"Error generating random ports: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while generating random ports: {str(e)}",
        )
