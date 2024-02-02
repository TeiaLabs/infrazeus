import argparse

def get_args():
    parser = argparse.ArgumentParser(description="ECR manager")
    parser.add_argument("--output", default="./deployment/")
    # Subparsers container for actions
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # Subparser for create action
    create_parser = subparsers.add_parser("create", help="Create a resource")
    create_input = create_parser.add_subparsers(dest="input_type", help="Type of input for create action")
    
    # File input for create action
    create_file_input = create_input.add_parser("file_input", help="Specify a file input for create action")
    create_file_input.add_argument("--file", required=True, help="Path to the input file for create action")
    
    # Manual input for create action
    create_manual_input = create_input.add_parser("manual_input", help="Provide manual input for create action")
    create_manual_input.add_argument('--service_name', type=str, required=True, help='Service name for create action')
    create_manual_input.add_argument('--environment', type=str, required=True, help='Service environment.')
    create_manual_input.add_argument('--region', type=str, required=True, help='AWS region.')

    # Subparser for delete action
    delete_parser = subparsers.add_parser("delete", help="Delete a resource")
    delete_input = delete_parser.add_subparsers(dest="input_type", help="Type of input for delete action")
    
    # File input for delete action
    delete_file_input = delete_input.add_parser("file_input", help="Specify a file input for delete action")
    delete_file_input.add_argument("--file", required=True, help="Path to the input file for delete action")
    
    # Manual input for delete action
    delete_manual_input = delete_input.add_parser("manual_input", help="Provide manual input for delete action")
    delete_manual_input.add_argument('--service_name', type=str, required=True, help='Service name for delete action')

    # Add similar subparsers for the list action if needed

    return parser
