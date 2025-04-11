import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.chmod_models import (
    ChmodNumericInput,
    ChmodNumericOutput,
    ChmodPermission,
    ChmodSymbolicInput,
    ChmodSymbolicOutput,
)
from routers.chmod_router import router as chmod_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chmod_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Numeric chmod Calculation ---


@pytest.mark.parametrize(
    "owner_perms, group_perms, other_perms, expected_numeric",
    [
        # Full permissions
        (
            ChmodPermission(read=True, write=True, execute=True),
            ChmodPermission(read=True, write=True, execute=True),
            ChmodPermission(read=True, write=True, execute=True),
            "777",
        ),
        # Common permissions
        (
            ChmodPermission(read=True, write=True, execute=True),
            ChmodPermission(read=True, execute=True),
            ChmodPermission(read=True, execute=True),
            "755",
        ),
        (ChmodPermission(read=True, write=True), ChmodPermission(read=True), ChmodPermission(read=True), "644"),
        (ChmodPermission(read=True, write=True), ChmodPermission(read=True, write=True), ChmodPermission(), "660"),
        # No permissions
        (ChmodPermission(), ChmodPermission(), ChmodPermission(), "000"),
        # Write only (uncommon but valid)
        (ChmodPermission(write=True), ChmodPermission(write=True), ChmodPermission(write=True), "222"),
        # Execute only (uncommon but valid)
        (ChmodPermission(execute=True), ChmodPermission(execute=True), ChmodPermission(execute=True), "111"),
        # Mixed
        (ChmodPermission(read=True, execute=True), ChmodPermission(write=True), ChmodPermission(read=True), "524"),
    ],
)
@pytest.mark.asyncio
async def test_chmod_calculate_numeric_success(
    client: TestClient,
    owner_perms: ChmodPermission,
    group_perms: ChmodPermission,
    other_perms: ChmodPermission,
    expected_numeric: str,
):
    """Test successful calculation of numeric chmod values."""
    payload = ChmodNumericInput(owner=owner_perms, group=group_perms, others=other_perms)
    response = client.post("/api/chmod/calculate-numeric", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = ChmodNumericOutput(**response.json())
    assert output.numeric == expected_numeric


# --- Test Symbolic chmod Calculation ---


@pytest.mark.parametrize(
    "numeric_input, expected_symbolic",
    [
        (777, "rwxrwxrwx"),
        ("777", "rwxrwxrwx"),
        (755, "rwxr-xr-x"),
        ("0755", "rwxr-xr-x"),  # Test with leading zero
        (644, "rw-r--r--"),
        ("644", "rw-r--r--"),
        (660, "rw-rw----"),
        (0, "---------"),
        ("000", "---------"),
        (111, "--x--x--x"),
        (222, "-w--w--w-"),
        (444, "r--r--r--"),
        (524, "r-x-w-r--"),
    ],
)
@pytest.mark.asyncio
async def test_chmod_calculate_symbolic_success(client: TestClient, numeric_input: int | str, expected_symbolic: str):
    """Test successful calculation of symbolic chmod representation."""
    payload = ChmodSymbolicInput(numeric=numeric_input)
    response = client.post("/api/chmod/calculate-symbolic", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = ChmodSymbolicOutput(**response.json())
    assert output.symbolic == expected_symbolic


@pytest.mark.parametrize(
    "invalid_numeric_input, expected_error_detail",
    [
        (
            "abc",
            "Invalid numeric input: Numeric value must be 3 digits (e.g., 755 or 0755) or a single valid digit (0-7).",
        ),
        (
            12,
            "Invalid numeric input: Numeric value must be 3 digits (e.g., 755 or 0755) or a single valid digit (0-7).",
        ),
        (
            "12",
            "Invalid numeric input: Numeric value must be 3 digits (e.g., 755 or 0755) or a single valid digit (0-7).",
        ),
        (
            7777,
            "Invalid numeric input: Numeric value must be 3 digits (e.g., 755 or 0755) or a single valid digit (0-7).",
        ),
        (
            "01234",
            "Invalid numeric input: Numeric value must be 3 digits (e.g., 755 or 0755) or a single valid digit (0-7).",
        ),
        (800, "Invalid numeric input: Each digit must be between 0 and 7."),
        ("785", "Invalid numeric input: Each digit must be between 0 and 7."),
        ("759", "Invalid numeric input: Each digit must be between 0 and 7."),
        (
            -10,
            "Invalid numeric input: Numeric value must be 3 digits (e.g., 755 or 0755) or a single valid digit (0-7).",
        ),  # Caught by isdigit
    ],
)
@pytest.mark.asyncio
async def test_chmod_calculate_symbolic_invalid_input(
    client: TestClient, invalid_numeric_input: int | str, expected_error_detail: str
):
    """Test symbolic calculation with invalid numeric inputs."""
    payload = ChmodSymbolicInput(numeric=invalid_numeric_input)
    response = client.post("/api/chmod/calculate-symbolic", json=payload.model_dump())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"].lower() == expected_error_detail.lower()
