from rich import print 
from rich.console import Console

console = Console()


def print_stack_outputs(stack_output: dict[str, list], verbose: bool = False):
    non_verbose_keys = [
        "StackName",
        "StackStatus",
        "CreationTime",
        "Outputs",
    ]
    for stack in stack_output.get("Stacks", []):
        if verbose:
            for key, value in stack.items():
                print(f"{key}: {value}")
            continue
        
        for key in non_verbose_keys:
            print(f"{key}: {stack.get(key)}")


def lightning_decorator(n=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            lightning_emoji = '⚡'  # You can use a different emoji if necessary
            lightning_str = lightning_emoji * n
            # Modify the first and last argument to include the lightning strings
            args = (f"{lightning_str} {args[0]}",) + args[1:]
            args = args[:-1] + (f"{args[-1]}",)
            return func(*args, **kwargs)
        return wrapper
    return decorator
