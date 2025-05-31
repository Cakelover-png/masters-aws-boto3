import argparse
from core.utils.vpc.handlers import BaseVPCCommandHandler
from tasks8.utils.vpc import create_vpc_with_multiple_subnets

class CreateVPCWithMultipleSubnetsHandler(BaseVPCCommandHandler):
    """Handles creating a complete VPC setup with N public and N private subnets."""

    def execute(self, args: argparse.Namespace):
        """Execute the complete VPC creation process with multiple subnets."""
        
        if args.num_subnets > 200:
            print("Error: Maximum number of subnets is limited to 200.")
            return
        
        if args.num_subnets < 1:
            print("Error: Number of subnets must be at least 1.")
            return

        success, vpc_info = create_vpc_with_multiple_subnets(
            ec2_client=self.client,
            vpc_name=args.vpc_name,
            vpc_cidr=args.vpc_cidr,
            num_subnets=args.num_subnets,
            availability_zones=args.availability_zones
        )

        if success:
            print(f"Successfully created VPC setup '{args.vpc_name}' with {args.num_subnets} public and {args.num_subnets} private subnets")
            print(f"VPC ID: {vpc_info['vpc_id']}")
            print(f"Internet Gateway ID: {vpc_info['igw_id']}")
            print(f"Public Route Table ID: {vpc_info['public_route_table_id']}")
            print(f"Private Route Table ID: {vpc_info['private_route_table_id']}")
            
            print("\nPublic Subnets:")
            for i, subnet_id in enumerate(vpc_info['public_subnet_ids'], 1):
                print(f"  Public Subnet {i}: {subnet_id}")
            
            print("\nPrivate Subnets:")
            for i, subnet_id in enumerate(vpc_info['private_subnet_ids'], 1):
                print(f"  Private Subnet {i}: {subnet_id}")
        else:
            print(f"Failed to create VPC setup '{args.vpc_name}' with multiple subnets.")
