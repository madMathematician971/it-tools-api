from pydantic import BaseModel, Field


class DockerRunToComposeInput(BaseModel):
    docker_run_command: str = Field(..., description="The full 'docker run ...' command string")


class DockerRunToComposeOutput(BaseModel):
    docker_compose_yaml: str
