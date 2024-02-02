import boto3
from rich import print
from typing import Optional, Any, Dict, List
from loguru import logger

from ..schema import Service


def create_ecr(service: Service) -> Optional[dict[str, Any]]:
    ecr_client = boto3.client('ecr', region_name=service.region)

    logger.info(f"Creating ECR repo named: {service.canonical_name}")
    try:
        response = ecr_client.create_repository(
            repositoryName=service.canonical_name
        )
        return response
    except ecr_client.exceptions.RepositoryAlreadyExistsException:
        print(f"Repository {service.canonical_name} already exists.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def list_ecr(name_contains: Optional[str] = None, name_equals: Optional[str] = None) -> list[dict[str, Any]]:
    client = boto3.client('ecr')
    
    # Initialize the response array
    repositories: List[Dict[str, Any]] = []
    
    # Handle pagination in case there are many repositories
    paginator = client.get_paginator('describe_repositories')
    for page in paginator.paginate():
        for repo in page['repositories']:
            repo_name = repo['repositoryName']
            
            # Filter logic: check if the name should contain a substring or be equal to a given string
            if name_contains and name_contains in repo_name:
                repositories.append(repo)
            elif name_equals and name_equals == repo_name:
                repositories.append(repo)
            elif not name_contains and not name_equals:
                repositories.append(repo)

    return repositories


if __name__ == "__main__":
    service = Service(
        service_name="allai-chat-front",
        environment="beta",
        docker_tag="beta",
    )
    result = create_ecr(service)

