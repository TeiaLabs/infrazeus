from typing import Literal, Optional
from .args import get_args
from pathlib import Path

from .create_ecr import create_ecr_to_disk
from ..schema import Service


from dataclasses import dataclass


@dataclass
class CreateECR:
    service_name: str
    environment: Literal["beta", "staging", "prod"]
    region: str = "us-east-1"


@dataclass
class ListECR:
    service_name: Optional[str]
    service_name_contains: Optional[str]
    region: str = "us-east-1"


@dataclass
class DeleteECR:
    service_name: Optional[str]
    arn: Optional[str]
    region: str = "us-east-1"
    

if __name__ == "__main__":
    args = get_args().parse_args()
        # Parse the arguments
    # Now you can use args to access the arguments and subcommands
    # For example:
    
    if args.action == "create":
        if args.input_type == "file_input":
            service = Service.from_json(args.file)
        elif args.input_type == "manual_input":
            service = Service(
                service_name=args.service_name,
                environment=args.environment,
                region=args.region
            )
        else:
            raise ValueError("Invalid input type")

        create_ecr_to_disk(service, args.output)

    # elif args.action == "list":
    #     list_resources(args.region)
    # elif args.action == "delete":
    #     delete_resource(args.name, args.region)
    # else:
    #     parser.print_help()
