# Infra Creation with InfraZeus ⚡

<img src="resources/zeus.png" alt="InfraZeus Logo" width="500"/>

In this repo you will find the foundation scripts for divine cloud structures with AWS CloudFormation. 

## Getting Started

InfraZeus is a powerful tool designed to simplify the creation and management of your AWS infrastructure for deploying applications. 

It supports: 
- Creating Elastic Container Registry (ECR) repositories.
- Elastic Load Balancers (ALB).
- Parameters to parameter store and secret manager.
- Elastic Container Service (ECS) tasks.

### Set Up InfraZeus

Install Infrazeus:

```bash
git clone git@github.com:TeiaLabs/infrazeus.git
cd infrazeus
pip install .
```


### TLDR

Create a json file (e.g., `infrasets/my-service.beta.json`) with the following structure,:

```json
{
    "service_name": "plugins-api",
    "environment": "beta",
    "cluster": "allai-staging-services",
    "vpc": "vpc-0b4e5e8706197dec7",
    "docker_tag": "beta",
    "domain": "https://plugins.beta.allai.digital",
    "port": 443,
    "protocol": "HTTPS",
    "container_port": 5000,
    "cpu": 256,
    "memory": 2048
}
```

Create a .env file with all the variables the task will use when deployed (e.g., `infrasets/my-service.beta.env`):

```bash
PORT=80
RELOAD=True
SECRET_KEY=12345
...
```

Then run:

```bash
# Create the ECR repository
python -m infrazeus ecr create --file infrasets/my-service-api.beta.json

# ... run the github actions to build and push the docker image ...

# Create the Load balancer
python -m infrazeus alb create --file infrasets/my-service-api.beta.json

# Store parameters for the task
python -m infrazeus parameters create --file infrasets/my-service-api.beta.json --env infrasets/my-service-api.beta.env --secrets SECRET_KEY

# Create the ECS task
python -m infrazeus ecs create --file infrasets/my-service-api.beta.json
```

That's all. You can follow what's happening on the CloudFormation console.


## A more complete documentation

Use the InfraZeus tool by running it as a Python module with the following syntax:

```bash
python -m infrazeus <COMMAND> [OPTIONS]...
```

### Available Commands

Here is a list of available commands that InfraZeus supports:

- `alb`: Manage Application Load Balancers, with options to create, list, and describe stacks.
- `ecr`: Manage Elastic Container Registries, allowing you to create and list repositories.
- `ecs`: Manage Elastic Container Service tasks, including the creation, listing, and stack description.
- `parameters`: Handle environment parameters, offering creation and listing capabilities.

## Creating Infrastructure with InfraZeus

Using InfraZeus, you can seamlessly create an ECR repository, Application Load Balancers with SSL certification, and an ECS task for your application's Docker container. This includes automated environment variable management.

Before proceeding, ensure you have the following:

- A Docker image of your application.
- A `.env` file containing the production-ready environment variables.
- Configured AWS credentials.
- The necessary IAM permissions to create AWS resources such as ECR, ECS, Secrets Manager, ALB, security groups, and Certificate Manager.
- An SSL certificate for your domain (e.g., *.allai.digital, *.teialabs.com.br, *.osf.digital).

### Workflow Example

Here's an example workflow to illustrate how you can use InfraZeus to set up your infrastructure:

**Step 1: Create the ECR Repository**

Create an ECR repository by specifying the configuration file:

```bash
python -m infrazeus ecr create --file infrasets/service-example.json
```

After creation, push the Docker image to this repository, typically using GitHub Actions or your preferred CI/CD pipeline.

**Step 2: Create your Application Load Balancer**

To create a complete load balancer with target group, security group, and listeners with the SSL certificate run:

```bash
python -m infrazeus alb create --file infrasets/service-example.json 
```

**Step 3: Manage Application Environment Variables**

Upload your application environment variables to the AWS Systems Manager Parameter Store and AWS Secrets Manager:

```bash
python -m infrazeus parameters create --file infrasets/service-example.json --env infrasets/service-example.env --secrets MONGODB_URI
```

Specify your secret keys with the `--secrets` option.

**Step 4: Set Up Load Balancers and ECS Task**

Create the necessary Application Load Balancers (ALB) and an ECS task definition:

```bash
python -m infrazeus ecs create --file infrasets/service-example.json
```

**Step 4: Monitor Your Stack**

Check the status of the ECS services and related resources:

```bash
python -m infrazeus ecs describe_stack --file infrasets/service-example.json
```

For more detailed instructions or troubleshooting, refer to the relevant command sections in this document or access support through InfraZeus community channels.
