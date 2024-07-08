import json
from typing import Any, Dict, Optional

import boto3

from ..schema import Service


def detect_secrets_with_ai(service_variables: dict[str, str]):
    secret_keywords = ["mongodb_uri", "password", "api_key", "secret", "token", "key"]
    secret_dict = {
        key: value
        for key, value in service_variables.items()
        if any(keyword in key.lower() for keyword in secret_keywords)
    }
    return secret_dict


# %%
def create_secret(
    service: Service, service_variables: Dict[str, str]
) -> Optional[dict[str, Any]]:
    # Create a Secrets Manager client
    client = boto3.client("secretsmanager", region_name=service.region)

    # Construct the secret name
    secret_name = service.canonical_name

    # Convert the service_variables dictionary to a JSON string
    secret_string = json.dumps(service_variables)

    try:
        # Create the secret
        response = client.create_secret(
            Name=secret_name,
            Description=f"Secrets for {service.normalized_name} in {service.environment} environment [imported from .env with infrazeus].",
            SecretString=secret_string,
        )
        return response
    except client.exceptions.ResourceExistsException:
        response = client.update_secret(
            Description=f"Secrets for {service.normalized_name} in {service.environment} environment (imported from .env with infrazeus)",
            SecretId=secret_name,
            SecretString=secret_string,
        )
        return response
    except Exception as e:
        print(f"An error occurred: {e}")


def create_parameters(
    service: Service, service_variables: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    # Create a Systems Manager client
    client = boto3.client("ssm", region_name=service.region)

    responses = {}

    for key, value in service_variables.items():
        # Construct the parameter name for each key-value pair
        parameter_name = f"/{service.environment}/{service.normalized_name}/{key}"

        try:
            # Create or update the parameter
            response = client.put_parameter(
                Name=parameter_name,
                Description=f"{key} for {service.normalized_name} in {service.environment} environment",
                Value=value,
                Type="String",  # You can choose 'String', 'StringList', or 'SecureString'
                Overwrite=True,  # Set to True if you want to overwrite an existing parameter
            )
            responses[key] = response
        except client.exceptions.ParameterAlreadyExists:
            print(f"Parameter {parameter_name} already exists. Updating instead.")
            response = client.put_parameter(
                Name=parameter_name,
                Description=f"{key} for {service.normalized_name} in {service.environment} environment",
                Value=value,
                Type="String",  # You can choose 'String', 'StringList', or 'SecureString'
                Overwrite=True,  # Set to True if you want to overwrite an existing parameter
            )
            responses[key] = response
        except Exception as e:
            print(f"An error occurred while creating/updating parameter {key}: {e}")

    return responses
