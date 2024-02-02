from typing import Any, Optional
from ..schema import ALBService


def get_target_group_template(service: ALBService):
    return {
        'Resources': {
            'MyTargetGroup': {
                'Type': 'AWS::ElasticLoadBalancingV2::TargetGroup',
                'Properties': {
                    'Name': service.target_group_name,
                    'Protocol': 'HTTP',
                    'Port': service.container_port,
                    'TargetType': 'ip',
                    'VpcId': service.vpc,
                }
            },
        },
        'Outputs': {
            'TargetGroupArn': {
                'Description': 'ARN of the target group',
                'Value': {'Ref': 'MyTargetGroup'}
            },
        }
    }


def get_security_group_template(service: ALBService):
    return {
        'Resources': {
            'MySecurityGroup': {
                'Type': 'AWS::EC2::SecurityGroup',
                'Properties': {
                    'GroupName': service.sg_name,
                    'GroupDescription': f'ALB security group for {service.sg_name}',
                    'SecurityGroupIngress': [
                        {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'CidrIp': '0.0.0.0/0'},
                        {'IpProtocol': 'tcp', 'FromPort': service.port, 'ToPort': service.port, 'CidrIp': '0.0.0.0/0'},
                        {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'CidrIp': '0.0.0.0/0'}
                    ],
                    'VpcId': service.vpc,
                },
            }
        },
        'Outputs': {
            'SecurityGroupId': {
                'Description': 'ID of the security group',
                'Value': {'Ref': 'MySecurityGroup'}
            }
        }
    }


def get_alb_template(
    service: ALBService, 
    subnets: list[str],
) -> dict[str, Any]:
    """
        subnets: comma-separated list of strings
    """
    return {
        "Resources": {
            'MyLoadBalancer': {
                'Type': 'AWS::ElasticLoadBalancingV2::LoadBalancer',
                'Properties': {
                    'Name': service.alb_name,
                    'Subnets': subnets,
                    'SecurityGroups': [
                        {'Ref': 'MySecurityGroup'}
                    ],
                    'Scheme': 'internet-facing',
                    'Type': 'application',
                    'IpAddressType': 'ipv4'
                }
            },
        },
        'Outputs': {
            'LoadBalancerArn': {
                'Description': 'ARN of the load balancer',
                'Value': {'Ref': 'MyLoadBalancer'}
            },
        }
    }


def get_listener_template(
    service: ALBService,
    certificate_arn: str, 
    alb_arn: Optional[str] = None
):

    # Add the listener to the CloudFormation template
    base_template = {
        'Resources': {
            'MyHttpsListener':
            {
                'Type': 'AWS::ElasticLoadBalancingV2::Listener',
                'Properties': {
                    'DefaultActions': [
                        {
                            'Type': 'forward',
                            'TargetGroupArn': {'Ref': 'MyTargetGroup'}
                        }
                    ],
                    'LoadBalancerArn': {'Ref': 'MyLoadBalancer'},
                    'Port': service.port,
                    'Protocol': 'HTTPS',
                    'Certificates': [
                        {
                            'CertificateArn': certificate_arn
                        }
                    ]
                }
            }
        }
    }

    if alb_arn:
        base_template['Resources']['MyHttpsListener']['Properties']['LoadBalancerArn'] = alb_arn

    return base_template

