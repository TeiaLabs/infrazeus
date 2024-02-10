#!/usr/bin/env python
import typer
from pathlib import Path
from rich import print
from loguru import logger

from .alb.controller import reuse_alb, create_alb
from .aws.helper import subnet_ids_for_vpc, list_stack
from .cli_out import lightning_decorator, print_stack_outputs
from .ecr.controller import create_ecr, list_ecr
from .ecs.create import ECSBuilds
from .schema import Service, ALBService, ECSService



logger.level("INFO")

# Apply the decorator to the print method of the rich console
print = lightning_decorator(n=1)(print)

print("Welcome to Infrazeus!")

app = typer.Typer()

ecr_app = typer.Typer()
app.add_typer(ecr_app, name="ecr")

@ecr_app.command("create")
def ecr_create(file: str = typer.Option(..., "--file", "-f", help="Path to the file")):
    """
    Create an ECR repository from a file specification.
    """
    print(f"ECR create with file: {file}")
    service = Service.from_path(file)
    create_ecr(service)  # Assuming create_ecr is defined elsewhere


@ecr_app.command("list")
def ecr_list(
    name_contains: str = typer.Option(
        None, "--name-contains", "-n", help="Filter by name"),
    file: str = typer.Option(
        None, "--file", "-f", help="Path to the file"
    )):
    """
    List all ECR repositories.
    """
    repos = []
    if file:
        service = Service.from_path(file)
        print(f"Listing ECR repositories for {service.ecr_name}")
        repos = list_ecr(name_equals=service.ecr_name)
    if name_contains:
        print(f"Listing ECR repos for names that contain: {name_contains}")
        repos = list_ecr(name_contains=name_contains)

    print("Repos found:", repos)

ecs_app = typer.Typer()
app.add_typer(ecs_app, name="ecs")

@ecs_app.command("create")
def ecs_create(
    file: str = typer.Option(..., "--file", "-f", help="Path to the file"),
    build: ECSBuilds = typer.Option(ECSBuilds.BOTH.value, "--build", "-b", help="Specify the build process"),
    alb_name: str = typer.Option(None, "--alb-name", "-a", help="Specify the ALB name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Perform a dry run without applying changes"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    stack_suffix: str = typer.Option(None, "--stack-name-suffix", "-s", help="Suffix to concat to the auto stack name"),
):
    """
    Create ECS command.
    """
    from .ecs import create
    service = ECSService.from_path(file)
    print(service)
    print(build)
    create.main_create_ens(
        service=service, 
        alb_name=alb_name,
        build=build,
        verbose=verbose,
        dry_run=dry_run,
        stack_sufix=stack_suffix,
    )

    print(f"ECS create with file: {file}, build: {build}, alb_name: {alb_name}, dry_run: {dry_run}")


@ecs_app.command("describe_stack")
def ecs_describe_stack(
    file: str = typer.Option(..., "--file", "-f", help="Path to the file"),
    stack_suffix: str = typer.Option(None, "--stack-name-suffix", "-s", help="Suffix to concat to the auto stack name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Create ECS command.
    """
    service = ECSService.from_path(file)
    stack_name = service.stack_name(suffix=stack_suffix)
    print(f"Describe stack: {stack_name}")
    stack_out = list_stack(stack_name)
    print_stack_outputs(stack_out, verbose)

        
@ecs_app.command("update")
def ecs_update(file: str = typer.Option(..., "--file", "-f", help="Path to the file")):
    """
    Update ECS command.
    """
    print(f"No supported yet. Sorry.")


alb_app = typer.Typer()
app.add_typer(alb_app, name="alb")

@alb_app.command("create")
def alb_create(
    file: str = typer.Option(..., "--file", "-f", help="Path to the file"),
    suffix: str = typer.Option(None, "--stack-name-suffix", "-s", help="Suffix to concat to the auto stack name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Perform a dry run without applying changes"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):

    """
    Create ALB command.
    """
    service = ALBService.from_path(file)
    subnets = subnet_ids_for_vpc(
        service.vpc, unique_availability_zones=True
    )

    print(f"Create ALB: {service.alb_name} for service: {service}")
    print(f"Subnets available: {subnets}")

    if not subnets or len(subnets) < 2:
        print("ALB requires at least 2 subnets in different availability zones for VPC:", service.vpc)
        raise typer.Exit(code=1)

    response = create_alb(
        dry_run=dry_run,
        subnets=subnets,
        service=service,
        stack_suffix=suffix,
        verbose=verbose,
    )
    print(f"Stack response: {response}")


@alb_app.command("reuse")
def alb_reuse(
    file: str = typer.Option(..., "--file", "-f", help="Path to the file"),
    alb_name: str = typer.Option(..., "--alb-name", "-n", help="Specify the ALB name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Perform a dry run without applying changes")
):
    """
    Reuse ALB command.
    """
    print(f"ALB reuse with file: {file}, alb_name: {alb_name}, dry_run: {dry_run}")
    service = ALBService.from_path(file)
    reuse_alb(
        alb_name=alb_name,
        dry_run=dry_run,
        service=service,
    )


@alb_app.command("describe_stack")
def alb_describe_stack(
    file: str = typer.Option(..., "--file", "-f", help="Path to the file"),
    stack_suffix: str = typer.Option(None, "--stack-name-suffix", "-s", help="Suffix to concat to the auto stack name"),
    verbose: bool = typer.Option(False, "--dry-run", help="Perform a dry run without applying changes")
):
    """
    Reuse ALB command.
    """
    service = ALBService.from_path(file)
    stack_name = service.stack_name(suffix=stack_suffix)
    print(f"Describe stack: {stack_name}")
    stack_out = list_stack(stack_name)
    print_stack_outputs(stack_out, verbose)


params_app = typer.Typer()
app.add_typer(params_app, name="parameters")

@params_app.command("create")
def parameters_create(
    file: str = typer.Option(..., "--file", "-f", help="Path to the file"),
    env: Path = typer.Option(..., "--env", "-e", help="Environment file. It has to be a `.env` file."),
    secrets: list[str] = typer.Option(None, "--secrets", "-s", help="List of secret variables"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    Create parameters command.
    """
    from .parameters.create import create_parameters, create_secret, detect_secrets_with_ai
    from .parameters.env_handler import load_env_to_dict

    print(f"Parameters create with file: {file}, env: {env} and secrets: {secrets}")

    service = ECSService.from_path(file)
    evn_vars = load_env_to_dict(env)

    if not secrets or secrets is None:
        secret_vars = detect_secrets_with_ai(evn_vars)
        print(f"Auto secrets: {secret_vars}")
    else:
        secret_vars = {
            secret: f"{evn_vars[secret]}" 
            for secret in secrets if secret in evn_vars
        }
        missing_secrets = set(secrets) - set(secret_vars)
        if missing_secrets:
            logger.warning(f"Secrets informed not found in env vars: {missing_secrets}")

    not_secret_vars = {var: evn_vars[var] for var in evn_vars if var not in secret_vars}

    if verbose:
        print(f"Storing secrets: {secret_vars.keys()}")
        print(f"Storing non-secrets: {not_secret_vars.keys()}")

    all_var_values = {**secret_vars, **not_secret_vars}

    if not any([
        str(service.container_port) in f"{x}" 
        for x in all_var_values.values()
    ]):
        print(f"Container port: {service.container_port} not found in any environment variables. Please add it to the `.env` file.")
        raise typer.Exit(code=1)

    if secret_vars:
        secret_return = create_secret(service=service, service_variables=secret_vars)
        if verbose:
            print(f"Secret return: {secret_return}")

    if not_secret_vars:
        param_return = create_parameters(service=service, service_variables=not_secret_vars)
        if verbose:
            print(f"Parameters return: {param_return}")


@params_app.command("list")
def parameters_list(
    file: str = typer.Option(..., "--file", "-f", help="Path to the file"),
    show_values: bool = typer.Option(False, "--show-values", "-s", help="Show values"),
):
    """
    Create parameters command.
    """
    from .parameters.list import list_parameters, list_secrets
    from .parameters.env_handler import load_env_to_dict

    service = Service.from_path(file)

    print(f"Listing parameters for service: {service}")

    param_keys = list_parameters(service=service)
    secret_keys = list_secrets(service=service, show_values=show_values)

    print(f"Parameters: {param_keys}")
    print(f"Secrets: {secret_keys}")


workflow_app = typer.Typer()
app.add_typer(workflow_app, name="workflow")

@workflow_app.command("create")
def workflow_create(
    file: str = typer.Option(..., "--file", "-f", help="Path to the file"),
    workflow_file: Path = typer.Option(..., "--workflow_file", "-w", help="Path to the github workflow file"),
    output_file: Path = typer.Option(None, "--output_file", "-o", help="Path that the new file will be stored"),
    org: str = typer.Option(..., "--org", "-o", help="Org prefixed in the AWS var name (e.g., `OSF` for `OSF_AWS_SECRET_ACCESS_KEY`"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Perform a dry run without applying changes"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    
    print("This option is not implemented yet. Sorry :(")
    exit(1)
    """
    Create ALB command.
    """
    from .workflow.controller import update_github_action_workflow
    service = ECSService.from_path(file)

    if not output_file:
        # add org to the workflow_file name as fileprefix
        output_file = Path(workflow_file.parent / f"{org}_{workflow_file.name}")

    ret = update_github_action_workflow(
        org=org, service=service, 
        input_file_name=workflow_file, 
        output_file_name=output_file, 
        # dry_run=dry_run, 
        # verbose=verbose,
    )
    print(ret)


if __name__ == "__main__":
    app()
