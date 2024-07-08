import json
from pathlib import Path
from typing import Any, Dict, Optional

import boto3

from ..schema import Service
from .env_handler import load_env_to_dict


# Assuming the Service class and its subclasses are already defined as provided earlier.
def list_secrets(
    service: Service, show_values: bool = False
) -> Optional[dict[str, Any]]:
    # Create a Secrets Manager client
    client = boto3.client("secretsmanager", region_name=service.region)

    # Construct the secret name
    secret_name = (
        service.canonical_name
    )  # Assuming normalized_name is the correct attribute

    try:
        # Retrieve the secret value
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
            secret_dict = json.loads(secret)
            if not show_values:
                secret_dict = {key: "@SecretValue" for key in secret_dict.keys()}
            return secret_dict
        return None
    except client.exceptions.ResourceNotFoundException:
        print(f"Secret {secret_name} not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def list_parameters(service: Service) -> Optional[dict[str, Any]]:
    # Create a Systems Manager client
    client = boto3.client("ssm", region_name=service.region)

    # Construct the parameter name prefix
    parameter_prefix = f"/{service.environment}/{service.normalized_name}/"

    try:
        # Retrieve the parameters with the specified prefix
        paginator = client.get_paginator("describe_parameters")
        page_iterator = paginator.paginate(
            ParameterFilters=[
                {"Key": "Name", "Option": "BeginsWith", "Values": [parameter_prefix]}
            ]
        )
        parameter_content = {}
        for page in page_iterator:
            for param in page["Parameters"]:
                # Extract the parameter key from the full name
                _, _, key = param["Name"].rpartition("/")
                # Retrieve the parameter value
                parameter_value_response = client.get_parameter(
                    Name=param["Name"], WithDecryption=True
                )
                parameter_content[key] = parameter_value_response["Parameter"]["Value"]
        return parameter_content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
