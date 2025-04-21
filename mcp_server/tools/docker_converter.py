"""Tool for converting Docker commands."""

import logging
import shlex
from typing import Any

import yaml

from mcp_server import mcp_app

logger = logging.getLogger(__name__)


@mcp_app.tool()
def convert_run_to_compose(docker_run_command: str) -> dict[str, Any]:
    """
    Convert a 'docker run' command string into a docker-compose YAML structure.

    Args:
        docker_run_command: The 'docker run ...' command string.

    Returns:
        A dictionary containing:
            docker_compose_yaml: The generated YAML string.
            error: An error message string if conversion failed, otherwise None.
    """
    command_string = docker_run_command.strip()
    if not command_string.startswith("docker run"):
        return {"docker_compose_yaml": None, "error": "Input must be a valid 'docker run ...' command."}

    try:
        # Remove 'docker run ' prefix and split
        args_list = shlex.split(command_string[len("docker run") :].strip())
    except ValueError as e:
        return {"docker_compose_yaml": None, "error": f"Error splitting command: {e}"}

    # --- Manual Argument Parsing ---
    options: dict[str, Any] = {
        "ports": [],
        "volumes": [],
        "environment": [],
        "name": None,
        "restart": None,
        "detach": False,  # Not directly used in compose output, but parsed
    }
    image = None
    command: list[str] = []
    i = 0
    while i < len(args_list):
        arg = args_list[i]

        if arg in ("-p", "--publish"):
            if i + 1 < len(args_list):
                options["ports"].append(args_list[i + 1])
                i += 1
            else:
                return {"docker_compose_yaml": None, "error": f"Missing value for option {arg}"}
        elif arg in ("-v", "--volume"):
            if i + 1 < len(args_list):
                options["volumes"].append(args_list[i + 1])
                i += 1
            else:
                return {"docker_compose_yaml": None, "error": f"Missing value for option {arg}"}
        elif arg in ("-e", "--env"):
            if i + 1 < len(args_list):
                options["environment"].append(args_list[i + 1])
                i += 1
            else:
                return {"docker_compose_yaml": None, "error": f"Missing value for option {arg}"}
        elif arg == "--name":
            if i + 1 < len(args_list):
                options["name"] = args_list[i + 1]
                i += 1
            else:
                return {"docker_compose_yaml": None, "error": f"Missing value for option {arg}"}
        elif arg == "--restart":
            if i + 1 < len(args_list):
                options["restart"] = args_list[i + 1]
                i += 1
            else:
                return {"docker_compose_yaml": None, "error": f"Missing value for option {arg}"}
        elif arg in ("-d", "--detach"):
            options["detach"] = True
        elif not arg.startswith("-"):
            # Assume first non-option is the image, rest is command
            image = arg
            command = args_list[i + 1 :]
            break  # Stop processing arguments once image is found
        else:
            # Unknown option
            return {"docker_compose_yaml": None, "error": f"Unrecognized option: {arg}"}

        i += 1

    if not image:
        return {"docker_compose_yaml": None, "error": "Missing image name"}

    # --- Build Compose Dictionary ---
    # Basic service name generation
    service_name = options["name"] if options["name"] else image.split(":")[0].split("/")[-1]
    service_config: dict[str, Any] = {"image": image}

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

    compose_dict: dict[str, Any] = {"services": {service_name: service_config}}

    # --- Generate YAML ---
    try:
        # Use sort_keys=False to maintain insertion order appearance
        output_yaml = yaml.dump(compose_dict, default_flow_style=False, sort_keys=False)
        return {"docker_compose_yaml": output_yaml, "error": None}
    except Exception as e:
        logger.error(f"Error generating YAML: {e}", exc_info=True)
        return {"docker_compose_yaml": None, "error": f"Internal server error during YAML generation: {str(e)}"}
