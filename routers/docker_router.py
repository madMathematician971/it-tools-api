import logging

from fastapi import APIRouter, HTTPException, status

from mcp_server.tools.docker_converter import convert_run_to_compose
from models.docker_models import DockerRunToComposeInput, DockerRunToComposeOutput

router = APIRouter(prefix="/api/docker", tags=["Docker"])

logger = logging.getLogger(__name__)


@router.post("/run-to-compose", response_model=DockerRunToComposeOutput)
async def docker_run_to_compose_endpoint(payload: DockerRunToComposeInput):
    """Convert a 'docker run' command into a docker-compose YAML structure using the MCP tool."""
    command_string = payload.docker_run_command

    try:
        # Call the tool function
        result = convert_run_to_compose(docker_run_command=command_string)

        # Check if the tool returned an error
        if error := result.get("error"):
            logger.warning(f"Docker run to compose tool failed for command '{command_string}': {error}")
            # Determine appropriate HTTP status code based on error type
            if (
                "Input must be a valid" in error
                or "Missing value for option" in error
                or "Error splitting command" in error
                or "Missing image name" in error
                or "Unrecognized option" in error
            ):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input: {error}")
            # Default to internal server error for unexpected tool errors
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Tool error: {error}")

        # Return the YAML if successful
        output_yaml = result.get("docker_compose_yaml")
        if output_yaml is None:
            # Should not happen if error is None, but safeguard
            logger.error("Tool returned no error but also no YAML.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error: Tool failed to produce YAML."
            )

        return {"docker_compose_yaml": output_yaml}

    except HTTPException as e:
        # Re-raise HTTP exceptions directly
        raise e
    except Exception as e:
        # Catch unexpected errors during the process
        logger.error(f"Unexpected error converting docker run command: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
