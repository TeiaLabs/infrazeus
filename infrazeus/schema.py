import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import boto3
from pydantic import BaseModel, Field


def get_account_id():
    # Assuming you have the AWS credentials configured in your environment or config file
    sts_client = boto3.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    return account_id


def get_default_region():
    # This will retrieve the default region name from the AWS config or environment variable
    return boto3.session.Session().region_name or "us-east-1"


class Service(BaseModel):
    account_id: str = Field(default_factory=get_account_id)
    service_name: str
    environment: Literal["beta", "staging", "prod"]
    docker_tag: Optional[str] = None
    name_for_human: Optional[str] = None
    region: str = Field(default_factory=get_default_region)

    @property
    def normalized_name(self) -> str:
        return self.service_name.lower().replace("_", "-").replace(" ", "-")

    @property
    def canonical_name(self) -> str:
        return f"{self.normalized_name}-{self.environment}"

    @property
    def ecr_name(self) -> str:
        return self.canonical_name

    @property
    def sg_name(self) -> str:
        return f"{self.canonical_name}-sg"

    @property
    def alb_name(self) -> str:
        return f"{self.canonical_name}-alb"

    @property
    def target_group_name(self) -> str:
        return f"{self.canonical_name}-tg"

    @classmethod
    def from_path(cls, json_file_path: str | Path):
        return cls(**json.load(open(json_file_path)))

    @property
    def ecr_image_path(
        self,
    ) -> str:
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.ecr_name}:{self.docker_tag}"


class ALBService(Service):
    cluster: Optional[str]
    vpc: str
    domain: Optional[str] = None
    port: int = 80
    container_port: int = 80
    protocol: Literal["HTTP", "HTTPS"]

    def stack_name(self, suffix: Optional[str]) -> str:
        name = f"{self.canonical_name}-alb-stack"
        if suffix:
            name = f"{name}-{suffix}"
        return name


class ECSService(ALBService):
    container_port: int
    memory: int
    cpu: int

    def stack_name(self, suffix: Optional[str]) -> str:
        name = f"{self.canonical_name}-ecs-stack"
        if suffix:
            name = f"{name}-{suffix}"
        return name
