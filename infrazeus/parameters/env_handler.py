import json
from pathlib import Path


def load_env_to_dict(env_file_path: Path) -> dict[str, str]:
    """
    Reads a .env file and converts it into a dictionary.

    Parameters:
    env_file_path (str): The path to the .env file.

    Returns:
    dict: A dictionary with key-value pairs from the .env file.
    """
    if not env_file_path.exists():
        raise FileNotFoundError(f"Could not find .env file at {env_file_path}")

    # if not .env file 
    if env_file_path.suffix != '.env':
        raise ValueError(f"Expected .env file, got {env_file_path.suffix}")

    env_vars = {}
    with open(env_file_path, 'r') as file:
        for line in file:
            # Strip whitespace and ignore lines that are empty or start with a comment
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                except ValueError:
                    print(f"Warning: Ignoring malformed line: {line}")
    return env_vars


def load_json(json_env_file) -> dict[str, str]:
    with open(json_env_file, 'r') as file:
        return json.load(file)


def load_env_vars(env_var_file: Path) -> dict[str, str]:
    # if not .env file 
    if env_var_file.suffix in ['.env']:
        return load_env_to_dict(env_var_file)   
    
    elif env_var_file.suffix in ['.json']:
        return load_json(env_var_file)

    else:
        raise ValueError(f"Expected .env or .json file, got {env_var_file.suffix}")