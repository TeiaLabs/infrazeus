from typing import Any
import boto3


def list_subnets(
    ec2_client,
    vpc_id: str,
    filter_available: bool = True,
    unique_availability_zones: bool = True,
    filter_public_subnets: bool = True
):
    # Describe subnets
    subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]) if vpc_id else ec2_client.describe_subnets()
    
    if "Subnets" in subnets:
        filtered_subnets = []
        seen_azs = set()

        # Describe route tables to check for public subnets
        route_tables = ec2_client.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]) if vpc_id else ec2_client.describe_route_tables()

        # Create a set of subnet IDs that are associated with a route to an Internet Gateway
        public_subnet_ids = set()
        for rt in route_tables['RouteTables']:
            for r in rt['Routes']:
                if r.get('GatewayId', '').startswith('igw-') and r.get('DestinationCidrBlock') == '0.0.0.0/0':
                    for assoc in rt.get('Associations', []):
                        if assoc.get('SubnetId'):
                            public_subnet_ids.add(assoc['SubnetId'])

        for subnet in subnets['Subnets']:
            # Filter out subnets that are not available if requested
            if filter_available and subnet['State'] != 'available':
                continue

            # Skip subnets from already seen availability zones if unique_availability_zones is True
            if unique_availability_zones and subnet['AvailabilityZone'] in seen_azs:
                continue

            # If filtering public subnets, skip subnets that are not in the public_subnet_ids set
            if filter_public_subnets and subnet['SubnetId'] not in public_subnet_ids:
                continue

            # The subnet passes the filters, add to result
            filtered_subnets.append(subnet)
            seen_azs.add(subnet['AvailabilityZone'])

        subnets = filtered_subnets

    return subnets


def subnet_ids_for_vpc(vpc: str, unique_availability_zones=False) -> list[str]:
    subnets = list_subnets(
        boto3.client('ec2'), vpc, 
        unique_availability_zones=unique_availability_zones
    )
    subnets = [subnet["SubnetId"] for subnet in subnets]
    return subnets


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
