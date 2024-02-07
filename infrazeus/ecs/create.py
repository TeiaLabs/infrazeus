from typing import Any, Literal, Optional
from enum import Enum

import boto3
from loguru import logger
from rich import print

from infrazeus.aws.helper import create_stack, list_stack

from . import templates as t
from .list import list_task_definition_by_name

from ..alb.controller import get_alb_resources
from ..alb.helper import get_load_balancer_subnet_ids
from ..parameters.list import list_parameters, list_secrets
from ..schema import ECSService


class ECSBuilds(Enum):
    ECS = "ecs"
    TASK_DEFINITION = "task_definition"
    BOTH = "both"


def main_create_ens(
    service: ECSService, 
    alb_name: Optional[str] = None, 
    build: Literal[ECSBuilds.ECS, ECSBuilds.TASK_DEFINITION, ECSBuilds.BOTH] = ECSBuilds.BOTH,
    verbose: bool = False,
    dry_run: bool = False,
    stack_sufix: Optional[str] = None,
) -> dict[str, Any]:

    cf_client = boto3.client('cloudformation')
    
    # Already existing ALB
    if alb_name:
        alb_resources = get_alb_resources(alb_name)
        if verbose:
            logger.info(f"Using existing ALB: {alb_name}\nALB Resources: {alb_resources}")

    # Try to get alb resources from stack created by infrazeus
    else:
        alb_stack_name = f'{service.service_name}-{service.environment}-alb-stack'
        alb_stack_outputs = cf_client.describe_stacks(StackName=alb_stack_name)
        print("alb stack out", alb_stack_outputs)
        alb_resources = alb_stack_outputs["Stacks"][0]["Outputs"]
        alb_resources = {output["OutputKey"]: output["OutputValue"] for output in alb_resources}
        alb_name = service.alb_name

    target_group_arn = alb_resources["TargetGroupArn"]
    security_group_id = alb_resources["SecurityGroupId"]
    
    if isinstance(security_group_id, str):
        security_group_id = [security_group_id,]

    load_balancer_arn = alb_resources["LoadBalancerArn"]

    subnets = get_load_balancer_subnet_ids(alb_name)

    ecr_path = service.ecr_image_path

    logger.info(f"ECR Path: {ecr_path}")
    logger.debug(f"Target Group ARN: {target_group_arn}")
    logger.debug(f"Security Group ID: {security_group_id}")
    logger.debug(f"Load Balancer ARN: {load_balancer_arn}")

    print(target_group_arn)
    print(security_group_id)
    print(load_balancer_arn)

    cf_client = boto3.client('cloudformation')
    
    template_head = t.get_template_head(
        service=service, 
        target_group_arn=target_group_arn,
        security_group_ids=security_group_id,
        subnets=subnets,
        ecr_image_arn=ecr_path,
        memory=service.memory,
        cpu=service.cpu,
    )

    if build.value == ECSBuilds.TASK_DEFINITION.value:
        task_definition_template = t.get_task_definition_template(
            service=service, 
            parameters=list_parameters(service),
            secrets=list_secrets(service)
        )
        template_head.update(task_definition_template["Resources"])
        logger.info(template_head)

    elif build.value == ECSBuilds.ECS.value:
        task_definition_arn = list_task_definition_by_name(service.canonical_name)
        if not task_definition_arn:
            logger.error(f"Could not find task definition for {service.canonical_name}")
            exit()

        template_head["Parameters"]["ECSTaskDefinition"] = {   
            'Type': 'String',
            'Description': 'Task definition to start the ECS task',
            'Default': task_definition_arn[0]
        }
        template_head.update(t.ECS_TEMPLATE)

    elif build.value == ECSBuilds.BOTH.value:
        task_definition_template = t.get_task_definition_template(
            service=service, 
            parameters=list_parameters(service),
            secrets=list_secrets(service)
        )
        template_head["Resources"] = task_definition_template["Resources"]
        template_head["Resources"].update(t.ECS_TEMPLATE["Resources"])
        # template_head["Outputs"] = {}
        template_head["Outputs"] = task_definition_template["Outputs"]
        template_head["Outputs"].update(t.ECS_TEMPLATE["Outputs"])

    else:
        raise ValueError(f"Invalid build type: {build}")

    print("\nCloudform template:")    
    print(template_head)

    if dry_run:
        return {}

    return create_stack(
        stack_name=service.stack_name(suffix=stack_sufix),
        template=template_head,  
    )


# def create_ecs(service: ECSService):    
#     sts_client = boto3.client('sts')
#     account_id = sts_client.get_caller_identity()["Account"]
#     logger.info(f"Using account: {account_id}")
