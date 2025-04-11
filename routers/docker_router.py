import logging
import shlex
from typing import Any, Dict, List

import yaml
from fastapi import APIRouter, HTTPException, status

from models.docker_models import DockerRunToComposeInput, DockerRunToComposeOutput

router = APIRouter(prefix="/api/docker", tags=["Docker"])

logger = logging.getLogger(__name__)


@router.post("/run-to-compose", response_model=DockerRunToComposeOutput)
async def docker_run_to_compose(payload: DockerRunToComposeInput):
    """Convert a 'docker run' command into a docker-compose YAML structure using manual parsing."""
    command_string = payload.docker_run_command.strip()
    if not command_string.startswith("docker run"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input must be a valid 'docker run ...' command.",
        )

    try:
        args_list = shlex.split(command_string[len("docker run") :].strip())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error splitting command: {e}")

    # --- Manual Argument Parsing ---
    options: Dict[str, Any] = {
        "ports": [],
        "volumes": [],
        "environment": [],
        "name": None,
        "restart": None,
        "detach": False,
    }
    image = None
    command: List[str] = []
    i = 0
    while i < len(args_list):
        arg = args_list[i]

        if arg in ("-p", "--publish"):
            if i + 1 < len(args_list):
                options["ports"].append(args_list[i + 1])
                i += 1
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing value for option {arg}")
        elif arg in ("-v", "--volume"):
            if i + 1 < len(args_list):
                options["volumes"].append(args_list[i + 1])
                i += 1
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing value for option {arg}")
        elif arg in ("-e", "--env"):
            if i + 1 < len(args_list):
                options["environment"].append(args_list[i + 1])
                i += 1
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing value for option {arg}")
        elif arg == "--name":
            if i + 1 < len(args_list):
                options["name"] = args_list[i + 1]
                i += 1
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing value for option {arg}")
        elif arg == "--restart":
            if i + 1 < len(args_list):
                options["restart"] = args_list[i + 1]
                i += 1
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing value for option {arg}")
        elif arg in ("-d", "--detach"):
            options["detach"] = True
        elif not arg.startswith("-"):
            # Assume first non-option is the image, rest is command
            image = arg
            command = args_list[i + 1 :]
            break  # Stop processing arguments once image is found
        else:
            # Unknown option
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unrecognized option: {arg}")

        i += 1

    if not image:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing image name")

    # --- Build Compose Dictionary ---
    service_name = options["name"] if options["name"] else image.split(":")[0].split("/")[-1]
    service_config: Dict[str, Any] = {"image": image}

    if options["ports"]:
        service_config["ports"] = options["ports"]
    if options["volumes"]:
        service_config["volumes"] = options["volumes"]
    if options["environment"]:
        service_config["environment"] = options["environment"]
    if options["name"]:
        service_config["container_name"] = options["name"]
    if options["restart"]:
        service_config["restart"] = options["restart"]
    if command:
        service_config["command"] = command

    # Note: The -d / --detach flag doesn't usually map directly to compose, ignored here.

    compose_dict = {"services": {service_name: service_config}}

    # --- Generate YAML ---
    try:
        output_yaml = yaml.dump(compose_dict, default_flow_style=False, sort_keys=False)
        return {"docker_compose_yaml": output_yaml}
    except Exception as e:
        logger.error(f"Error generating YAML: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during YAML generation: {str(e)}",
        )
