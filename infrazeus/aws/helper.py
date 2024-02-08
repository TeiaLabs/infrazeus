from typing import Any
import boto3

import boto3
from typing import List

def list_subnets(
    ec2_client,
    vpc_id: str,
    filter_available: bool = True,
    unique_availability_zones: bool = True,
    filter_public_subnets: bool = True
) -> List[dict]:
    # Describe subnets for the VPC, list all first
    subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']

    # Describe route tables for the VPC
    route_tables = ec2_client.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']

    # Find public subnets if required
    public_subnet_ids = set()
    if filter_public_subnets:
        for rt in route_tables:
            for r in rt['Routes']:
                if r.get('GatewayId', '').startswith('igw-') and r.get('DestinationCidrBlock') == '0.0.0.0/0':
                    for assoc in rt.get('Associations', []):
                        if assoc.get('SubnetId'):
                            public_subnet_ids.add(assoc['SubnetId'])

    filtered_subnets = []
    seen_azs = set()
    for subnet in subnets:
        # Filter subnets based on the specified conditions
        if ((filter_available and subnet['State'] != 'available') or
            (unique_availability_zones and subnet['AvailabilityZone'] in seen_azs) or
            (filter_public_subnets and subnet['SubnetId'] not in public_subnet_ids)):
            continue

        # The subnet satisfies all the filters, so we include it in the result
        filtered_subnets.append(subnet)
        # Keep track of seen availability zones
        seen_azs.add(subnet['AvailabilityZone'])

    return filtered_subnets


def subnet_ids_for_vpc(vpc: str, unique_availability_zones=False, minimal_ip_available: int = 8, num_subnets: int = 3) -> List[str]:
    # Get a list of subnets with their details
    ec2_client = boto3.client('ec2')
    subnets = list_subnets(
        ec2_client, vpc,
        unique_availability_zones=unique_availability_zones
    )

    # Filter subnets with at least minimal_ip_available addresses left and choose up to 3
    qualified_subnets = [
        subnet["SubnetId"]
        for subnet in subnets
        if subnet["AvailableIpAddressCount"] >= minimal_ip_available
    ]
    
    return qualified_subnets[:num_subnets]  # Return a maximum of 3 subnets


def list_certificates(search_string, region: str = "us-east-1"):
    # Initialize the Boto3 ACM client
    if search_string.startswith("https:"):
        search_string = search_string[8:]

    acm_client = boto3.client('acm', region_name=region) 

    # Initialize a variable to hold the certificates
    certificates_containing_string = []

    # Retrieve the list of certificates
    paginator = acm_client.get_paginator('list_certificates')
    for page in paginator.paginate():
        for certificate in page['CertificateSummaryList']:
            # Check if the certificate's domain name contains the search string
            if search_string in certificate['DomainName']:
                certificates_containing_string.append(certificate)

    return certificates_containing_string


def create_stack(template: dict[str, Any], stack_name: str) -> dict[str, Any]:
    import json
    template_json = json.dumps(template)
    cf_client = boto3.client('cloudformation')
    response = cf_client.create_stack(
        StackName=stack_name,
        TemplateBody=template_json,
        Parameters=[],
    )

    return response


def list_stack(stack_name: str):
    cf_client = boto3.client('cloudformation')
    stacks = cf_client.describe_stacks(StackName=stack_name)
    return stacks
