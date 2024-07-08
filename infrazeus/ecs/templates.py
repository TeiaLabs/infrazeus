from typing import Any, Optional

from ..schema import ECSService


# %%
# Define the CloudFormation template
def get_template_head(
    service: ECSService,
    target_group_arn: str,
    security_group_ids: list[str],
    subnets: list[str],
    ecr_image_arn: str,
    memory: int = 512,
    cpu: int = 256,
):

    head_ecs_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": f"ECS Service and Task Definition for {service.canonical_name}",
        "Parameters": {
            "ServiceName": {
                "Type": "String",
                "Description": "The name of the service",
                "Default": f"{service.canonical_name}",
            },
            "ECRImage": {
                "Type": "String",
                "Description": "The ECR image to use with the task",
                "Default": ecr_image_arn,
            },
            "ContainerPort": {
                "Type": "Number",
                "Description": "The port on the container to bind to",
                "Default": service.container_port,
            },
            "ClusterName": {
                "Type": "String",
                "Description": "The name of the ECS cluster",
                "Default": service.cluster,
            },
            "TargetGroup": {
                "Type": "String",
                "Description": "The name of the target group",
                "Default": target_group_arn,
            },
            "ECSMemory": {
                "Type": "Number",
                "Description": "Memory for the task",
                "Default": memory,
            },
            "ECSCPU": {
                "Type": "Number",
                "Description": "Memory for the task",
                "Default": cpu,
            },
            "TaskExecutionRoleArn": {
                "Type": "String",
                "Description": "The ARN of the task execution role",
                "Default": "arn:aws:iam::147431826892:role/ecsTaskExecutionRole",
            },
            "SecurityGroup": {
                "Type": "CommaDelimitedList",
                "Description": "Security groups",
                "Default": ",".join(security_group_ids * 2),
            },
            "Subnets": {
                "Type": "CommaDelimitedList",
                "Description": "Subnets",
                "Default": ",".join(subnets),
            },
            # Add other parameters as needed
        },
    }
    return head_ecs_template


def get_task_definition_template(
    service: ECSService,
    secrets: Optional[dict[str, Any]] = None,
    parameters: Optional[dict[str, Any]] = None,
):
    container_definitions = {
        "Name": {"Ref": "ServiceName"},
        "Image": {"Ref": "ECRImage"},
        "Essential": True,
        "Memory": {"Ref": "ECSMemory"},  # Adjust as needed
        "Cpu": {"Ref": "ECSCPU"},  # Adjust as needed
        "PortMappings": [
            {
                "ContainerPort": {"Ref": "ContainerPort"},
                "HostPort": {"Ref": "ContainerPort"},
            }
        ],
        "LogConfiguration": {
            "LogDriver": "awslogs",
            "Options": {
                "awslogs-group": f"/ecs/{service.environment}",
                "awslogs-region": {"Ref": "AWS::Region"},
                "awslogs-stream-prefix": {"Ref": "ServiceName"},
            },
        },
    }

    if parameters:
        container_definitions["Environment"] = [
            {
                "Name": key,
                "Value": value,
                # 'Value': f"/{service.environment}/{service.normalized_name}/{key}"
            }
            for key, value in parameters.items()
        ]

    if secrets:
        container_definitions["Secrets"] = [
            {
                "Name": key,
                "ValueFrom": (
                    f"arn:aws:secretsmanager:{service.region}:"
                    f"{service.account_id}:secret:{service.canonical_name}:{key}::"
                ),
            }
            for key in secrets.keys()
        ]

    task_definition_template = {
        "Resources": {
            "ECSTaskDefinition": {
                "Type": "AWS::ECS::TaskDefinition",
                "Properties": {
                    "Family": {"Ref": "ServiceName"},
                    "ContainerDefinitions": [container_definitions],
                    "RequiresCompatibilities": ["FARGATE"],
                    "NetworkMode": "awsvpc",
                    "Memory": {"Ref": "ECSMemory"},  # Adjust as needed
                    "Cpu": {"Ref": "ECSCPU"},  # Adjust as needed
                    "ExecutionRoleArn": {"Ref": "TaskExecutionRoleArn"},
                },
            },
        },
        "Outputs": {
            "TaskDefinitionArn": {
                "Description": "ARN of the task definition",
                "Value": {"Ref": "ECSTaskDefinition"},
            }
        },
    }

    return task_definition_template


ECS_TEMPLATE = {
    "Resources": {
        "ECSService": {
            "Type": "AWS::ECS::Service",
            "Properties": {
                "ServiceName": {"Ref": "ServiceName"},
                "Cluster": {"Ref": "ClusterName"},
                "TaskDefinition": {"Ref": "ECSTaskDefinition"},
                "DesiredCount": 1,  # Adjust as needed
                "LaunchType": "FARGATE",
                "SchedulingStrategy": "REPLICA",
                "NetworkConfiguration": {
                    "AwsvpcConfiguration": {
                        "AssignPublicIp": "ENABLED",
                        "SecurityGroups": {"Ref": "SecurityGroup"},
                        "Subnets": {"Ref": "Subnets"},
                    }
                },
                "LoadBalancers": [
                    {
                        "ContainerName": {"Ref": "ServiceName"},
                        "ContainerPort": {"Ref": "ContainerPort"},
                        "TargetGroupArn": {
                            "Ref": "TargetGroup"
                        },  # This should be a parameter or a resource reference
                    }
                ],
                "PlatformVersion": "LATEST",
                "DeploymentConfiguration": {
                    "MaximumPercent": 200,
                    "MinimumHealthyPercent": 100,
                    "DeploymentCircuitBreaker": {"Enable": True, "Rollback": True},
                },
                "DeploymentController": {"Type": "ECS"},
                "ServiceConnectConfiguration": {"Enabled": False},
                "Tags": [],
                "EnableECSManagedTags": False,
            },
        },
    },
    "Outputs": {
        "ServiceName": {
            "Description": "The name of the ECS service",
            "Value": {"Ref": "ECSService"},
        },
    },
}
