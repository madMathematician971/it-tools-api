import pytest
import yaml  # To parse the output YAML for comparison
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from models.docker_models import DockerRunToComposeInput, DockerRunToComposeOutput
from routers.docker_router import router as docker_router


# Fixture for the FastAPI app
@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(docker_router)
    return app


# Fixture for the TestClient
@pytest.fixture(scope="module")
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


# --- Test Docker Run to Compose Conversion ---


@pytest.mark.parametrize(
    "docker_run_command, expected_service_config",
    [
        # Basic image
        ("docker run nginx", {"services": {"nginx": {"image": "nginx"}}}),
        # Image with tag
        ("docker run redis:alpine", {"services": {"redis": {"image": "redis:alpine"}}}),
        # Port mapping
        (
            "docker run -p 8080:80 nginx",
            {"services": {"nginx": {"image": "nginx", "ports": ["8080:80"]}}},
        ),
        # Multiple port mappings
        (
            "docker run -p 8080:80 -p 443:443 myapp",
            {"services": {"myapp": {"image": "myapp", "ports": ["8080:80", "443:443"]}}},
        ),
        # Volume mapping
        (
            "docker run -v /data:/app/data mydataimage",
            {"services": {"mydataimage": {"image": "mydataimage", "volumes": ["/data:/app/data"]}}},
        ),
        # Named volume
        (
            "docker run -v myvolume:/data redis",
            {"services": {"redis": {"image": "redis", "volumes": ["myvolume:/data"]}}},
        ),
        # Environment variable
        (
            "docker run -e MYVAR=myvalue postgres",
            {"services": {"postgres": {"image": "postgres", "environment": ["MYVAR=myvalue"]}}},
        ),
        # Multiple environment variables
        (
            "docker run -e VAR1=val1 -e VAR2=val2 alpine",
            {"services": {"alpine": {"image": "alpine", "environment": ["VAR1=val1", "VAR2=val2"]}}},
        ),
        # Detached mode (-d is often ignored by Compose, but we parse it)
        ("docker run -d nginx", {"services": {"nginx": {"image": "nginx"}}}),
        # Container name (should become service name)
        (
            "docker run --name mycontainer nginx",
            {"services": {"mycontainer": {"image": "nginx", "container_name": "mycontainer"}}},
        ),
        # Restart policy
        (
            "docker run --restart always myapp",
            {"services": {"myapp": {"image": "myapp", "restart": "always"}}},
        ),
        # Command override
        (
            "docker run alpine echo hello",
            {"services": {"alpine": {"image": "alpine", "command": ["echo", "hello"]}}},
        ),
        # Complex example
        (
            "docker run -d --name web -p 80:80 -v $(pwd)/html:/usr/share/nginx/html --restart unless-stopped nginx:latest",
            {
                "services": {
                    "web": {
                        "image": "nginx:latest",
                        "container_name": "web",
                        "ports": ["80:80"],
                        "volumes": ["$(pwd)/html:/usr/share/nginx/html"],
                        "restart": "unless-stopped",
                    }
                }
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_docker_run_to_compose_success(
    client: TestClient, docker_run_command: str, expected_service_config: dict
):
    """Test successful conversion of various docker run commands."""
    payload = DockerRunToComposeInput(docker_run_command=docker_run_command)
    response = client.post("/api/docker/run-to-compose", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK
    output = DockerRunToComposeOutput(**response.json())

    # Parse the output YAML and compare with the expected structure
    try:
        parsed_yaml = yaml.safe_load(output.docker_compose_yaml)
        assert parsed_yaml == expected_service_config
    except yaml.YAMLError as e:
        pytest.fail(f"Output YAML could not be parsed: {e}\nYAML:\n{output.docker_compose_yaml}")


@pytest.mark.parametrize(
    "invalid_command, expected_status, error_substring",
    [
        ("docker build .", status.HTTP_400_BAD_REQUEST, "Input must be a valid 'docker run ...' command."),
        ("run nginx", status.HTTP_400_BAD_REQUEST, "Input must be a valid 'docker run ...' command."),
        ("docker run", status.HTTP_400_BAD_REQUEST, "Missing image name"),
        (
            "docker run -invalidoption nginx",
            status.HTTP_400_BAD_REQUEST,
            "Unrecognized option: -invalidoption",
        ),
        ("", status.HTTP_400_BAD_REQUEST, "Input must be a valid 'docker run ...' command."),
    ],
)
@pytest.mark.asyncio
async def test_docker_run_to_compose_invalid_input(
    client: TestClient, invalid_command: str, expected_status: int, error_substring: str
):
    """Test conversion attempts with invalid or non-'docker run' commands."""
    payload = DockerRunToComposeInput(docker_run_command=invalid_command)
    response = client.post("/api/docker/run-to-compose", json=payload.model_dump())

    assert response.status_code == expected_status
    assert error_substring in response.json()["detail"]
