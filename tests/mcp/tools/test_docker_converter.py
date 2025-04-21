"""Tests for the Docker command converter tool using pytest."""

import pytest  # pylint: disable=unused-import
import yaml

from mcp_server.tools.docker_converter import convert_run_to_compose


def test_simple_command():
    """Test a basic docker run command."""
    command = "docker run hello-world"
    expected_yaml = yaml.dump(
        {"services": {"hello-world": {"image": "hello-world"}}}, default_flow_style=False, sort_keys=False
    )
    result = convert_run_to_compose(command)
    assert result.get("error") is None
    assert result.get("docker_compose_yaml") == expected_yaml


def test_with_ports_volumes_env_name_restart():
    """Test a command with various options."""
    command = (
        "docker run -d --name my-nginx -p 8080:80 -v /data:/usr/share/nginx/html "
        "-e NGINX_HOST=example.com --restart always nginx:latest"
    )
    expected_config = {
        "image": "nginx:latest",
        "ports": ["8080:80"],
        "volumes": ["/data:/usr/share/nginx/html"],
        "environment": ["NGINX_HOST=example.com"],
        "container_name": "my-nginx",
        "restart": "always",
    }
    expected_yaml = yaml.dump({"services": {"my-nginx": expected_config}}, default_flow_style=False, sort_keys=False)
    result = convert_run_to_compose(command)
    assert result.get("error") is None
    # Compare parsed YAML to avoid whitespace/ordering issues if possible
    assert yaml.safe_load(result.get("docker_compose_yaml")) == yaml.safe_load(expected_yaml)


def test_with_command_args():
    """Test a command that includes arguments passed to the container."""
    command = "docker run ubuntu:latest echo 'Hello from container'"
    expected_config = {"image": "ubuntu:latest", "command": ["echo", "Hello from container"]}
    expected_yaml = yaml.dump({"services": {"ubuntu": expected_config}}, default_flow_style=False, sort_keys=False)
    result = convert_run_to_compose(command)
    assert result.get("error") is None
    assert yaml.safe_load(result.get("docker_compose_yaml")) == yaml.safe_load(expected_yaml)


def test_invalid_command_not_docker_run():
    """Test input that doesn't start with 'docker run'."""
    command = "docker ps -a"
    result = convert_run_to_compose(command)
    assert result.get("error") is not None
    assert "Input must be a valid 'docker run ...' command." in result.get("error")
    assert result.get("docker_compose_yaml") is None


def test_missing_image():
    """Test a command where the image name is missing."""
    command = "docker run -p 80:80"
    result = convert_run_to_compose(command)
    assert result.get("error") is not None
    assert "Missing image name" in result.get("error")
    assert result.get("docker_compose_yaml") is None


def test_missing_option_value():
    """Test a command where an option is missing its value."""
    command = "docker run -p"
    result = convert_run_to_compose(command)
    assert result.get("error") is not None
    assert "Missing value for option -p" in result.get("error")
    assert result.get("docker_compose_yaml") is None


def test_unrecognized_option():
    """Test a command with an option not handled by the parser."""
    command = "docker run --invalid-option hello-world"
    result = convert_run_to_compose(command)
    assert result.get("error") is not None
    assert "Unrecognized option: --invalid-option" in result.get("error")
    assert result.get("docker_compose_yaml") is None


def test_shlex_split_error():
    """Test command splitting failure."""
    command = "docker run ubuntu echo 'Unclosed quote"
    result = convert_run_to_compose(command)
    assert result.get("error") is not None
    assert "Error splitting command" in result.get("error")
    assert result.get("docker_compose_yaml") is None
