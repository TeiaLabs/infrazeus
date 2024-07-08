import boto3


# Function to get subnets for a given load balancer name
def get_load_balancer_subnet_ids(load_balancer_name) -> list[str]:

    # Initialize a boto3 ELB client
    elb_client = boto3.client("elbv2")

    # Describe the load balancers and filter by the load balancer name
    response = elb_client.describe_load_balancers(Names=[load_balancer_name])

    # Extract the load balancers
    load_balancers = response.get("LoadBalancers", [])

    # Assuming there is only one load balancer with the given name
    if load_balancers:
        # Extract the Availability Zones for the load balancer
        availability_zones = load_balancers[0].get("AvailabilityZones", [])

        # Extract the subnet IDs from the Availability Zones
        subnets = [az["SubnetId"] for az in availability_zones]
        return subnets
    else:
        # No load balancer found with the given name
        return []
