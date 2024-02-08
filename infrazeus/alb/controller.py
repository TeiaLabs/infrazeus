import json
import boto3
from typing import Optional
from botocore.exceptions import ClientError

from ..aws.helper import list_subnets, list_certificates, create_stack, list_stack
from ..schema import ALBService

from rich import print
from loguru import logger

from . import templates as t



def get_alb_resources(alb_name):
    # Create an ELBV2 client
    elbv2_client = boto3.client('elbv2')

    # Initialize the dictionary to store ALB resources
    dict_alb_resources = {}

    # Get the load balancer information
    load_balancers = elbv2_client.describe_load_balancers(Names=[alb_name])
    if load_balancers['LoadBalancers']:
        load_balancer = load_balancers['LoadBalancers'][0]
        dict_alb_resources['LoadBalancerArn'] = load_balancer['LoadBalancerArn']
        dict_alb_resources['SecurityGroupId'] = load_balancer['SecurityGroups']

    # Get the target groups associated with the load balancer
    target_groups = elbv2_client.describe_target_groups(LoadBalancerArn=dict_alb_resources['LoadBalancerArn'])
    if target_groups['TargetGroups']:
        target_group = target_groups['TargetGroups'][0]
        dict_alb_resources['TargetGroupArn'] = target_group['TargetGroupArn']

    return dict_alb_resources


def get_alb_arn_by_name(alb_name):
    # Create an ELBv2 client
    client = boto3.client('elbv2')
    
    try:
        # Retrieve all load balancers
        response = client.describe_load_balancers()
        
        # Look for the ALB with the specified name and return its ARN
        for load_balancer in response['LoadBalancers']:
            if load_balancer['LoadBalancerName'] == alb_name:
                return load_balancer['LoadBalancerArn']
        
        # If the ALB is not found, return a message indicating it
        return f"ALB named '{alb_name}' not found."
    
    except ClientError as e:
        # If there's an error from AWS, return the message
        return f"An error occurred: {e}"


def reuse_alb(
    alb_name: str, 
    service: ALBService, 
    dry_run: bool = False,
):

    cert = list_certificates(service.domain)
    logger.debug(f"All cert: {cert}")

    cert_arn = cert[0]["CertificateArn"]
    logger.info(f"Selected cert: {cert}")
    
    provided_alb_name = alb_name
    logger.debug(f"ALB name: {provided_alb_name}")
    alb_arn = get_alb_arn_by_name(provided_alb_name)
    logger.debug(f"ALB ARN: {alb_arn}")
    sg = t.get_security_group_template(service)
    logger.debug(f"SG: {sg}")
    tg = t.get_target_group_template(service)
    logger.debug(f"TG: {tg}")

    listen = t.get_listener_template(
        alb_arn=alb_arn,
        certificate_arn=cert_arn,
        service=service,
    )
    logger.debug(f"listener: {listen}")

    template = {
        'AWSTemplateFormatVersion': '2010-09-09',
        'Description': f'CloudFormation template for {service.normalized_name} based on existing {provided_alb_name} ALB',
        'Resources': {},
        'Outputs': {},
    }
    template["Resources"].update(sg["Resources"])
    template["Resources"].update(tg["Resources"])
    template["Resources"].update(listen["Resources"])
    template["Outputs"].update(sg["Outputs"])
    template["Outputs"].update(tg["Outputs"])

    print("Creation template:")
    print(template)

    if dry_run:
        exit()
    
    stack_name = f'{service.service_name}-{service.environment}-alb-reuse-{provided_alb_name}-stack-1'
    response = create_stack(template, stack_name)

    return response

    
def create_alb(
    service: ALBService,
    subnets: list[str],
    dry_run: bool = False,
    stack_suffix: Optional[str] = None,
    verbose: bool = False,
):
    
    domain = ".".join(service.domain.split(".")[-2:])
    cert = list_certificates(domain)

    cert_arn = cert[0]["CertificateArn"]
    logger.info(f"Selected SSL certificate: {cert}")

    # Get the ARN of the ALB
    provided_alb_name = service.alb_name
    alb_template = t.get_alb_template(
        service=service,
        subnets=subnets,
    )
    sg = t.get_security_group_template(service)
    tg = t.get_target_group_template(service)
    listen = t.get_listener_template(
        service=service, certificate_arn=cert_arn
    )

    if verbose:
        print("Security Group")
        print(sg)
        print("Target Group")
        print(tg)
        print("Listener")
        print(listen)
        print("Subnets")
        print(subnets)
    
    template = {
        'AWSTemplateFormatVersion': '2010-09-09',
        'Description': f'CloudFormation template for {service.normalized_name} based on existing {provided_alb_name} ALB',
        'Resources': {},
        'Outputs': {},
    }
    template["Resources"].update(alb_template["Resources"])
    template["Resources"].update(sg["Resources"])
    template["Resources"].update(tg["Resources"])
    template["Resources"].update(listen["Resources"])
    template["Outputs"].update(alb_template["Outputs"])
    template["Outputs"].update(sg["Outputs"])
    template["Outputs"].update(tg["Outputs"])

    if verbose:
        print(template)

    stack_name = service.stack_name(stack_suffix)

    if dry_run:
        return None

    response = create_stack(template, stack_name)
    return response
