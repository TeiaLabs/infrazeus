import boto3


def list_task_definition_by_name(task_name: str) -> list[str]:
    """
    List task definitions with the specified name.

    :param task_name: The name of the task definitions to list.
    :return: A list of task definition ARNs.
    """
    ecs_client = boto3.client('ecs')
    task_definitions = []

    # Paginator can help with handling more than 100 results
    paginator = ecs_client.get_paginator('list_task_definitions')
    for page in paginator.paginate(familyPrefix=task_name, status='ACTIVE', sort='DESC'):
        task_definitions.extend(page['taskDefinitionArns'])

    return task_definitions
