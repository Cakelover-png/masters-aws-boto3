import argparse

from core.utils.vpc.handlers import BaseVPCCommandHandler
from tasks7.utils.vpc import create_internet_gateway, create_route_table, create_subnet, create_vpc, create_vpc_with_subnets

class CreateCompleteVPCHandler(BaseVPCCommandHandler):
    """Handles creating a complete VPC setup with all components."""

    def execute(self, args: argparse.Namespace):
        """Execute the complete VPC creation process."""
        success, vpc_info = create_vpc_with_subnets(
            ec2_client=self.client,
            vpc_name=args.vpc_name,
            vpc_cidr=args.vpc_cidr,
            public_subnet_cidr=args.public_subnet_cidr,
            private_subnet_cidr=args.private_subnet_cidr,
            availability_zone=args.availability_zone
        )

        if success:
            print(f"Successfully created complete VPC setup '{args.vpc_name}'")
            print(f"VPC ID: {vpc_info['vpc_id']}")
            print(f"Internet Gateway ID: {vpc_info['igw_id']}")
            print(f"Public Subnet ID: {vpc_info['public_subnet_id']}")
            print(f"Private Subnet ID: {vpc_info['private_subnet_id']}")
            print(f"Public Route Table ID: {vpc_info['public_route_table_id']}")
            print(f"Private Route Table ID: {vpc_info['private_route_table_id']}")
        else:
            print(f"Failed to create complete VPC setup '{args.vpc_name}'.")


class CreateVPCHandler(BaseVPCCommandHandler):
    """Handles creating just a VPC."""

    def execute(self, args: argparse.Namespace):
        """Execute VPC creation."""
        success, vpc_id = create_vpc(
            ec2_client=self.client,
            vpc_name=args.vpc_name,
            vpc_cidr=args.vpc_cidr
        )

        if success:
            print(f"Successfully created VPC '{args.vpc_name}'")
            print(f"VPC ID: {vpc_id}")
        else:
            print(f"Failed to create VPC '{args.vpc_name}'.")


class CreateIGWHandler(BaseVPCCommandHandler):
    """Handles creating and attaching an Internet Gateway."""

    def execute(self, args: argparse.Namespace):
        """Execute Internet Gateway creation and attachment."""
        success, igw_id = create_internet_gateway(
            ec2_client=self.client,
            vpc_id=args.vpc_id,
            igw_name=args.igw_name
        )

        if success:
            print(f"Successfully created and attached Internet Gateway '{args.igw_name}'")
            print(f"Internet Gateway ID: {igw_id}")
            print(f"Attached to VPC: {args.vpc_id}")
        else:
            print(f"Failed to create Internet Gateway '{args.igw_name}'.")


class CreateSubnetHandler(BaseVPCCommandHandler):
    """Handles creating a subnet."""

    def execute(self, args: argparse.Namespace):
        """Execute subnet creation."""
        success, subnet_id = create_subnet(
            ec2_client=self.client,
            vpc_id=args.vpc_id,
            subnet_name=args.subnet_name,
            subnet_cidr=args.subnet_cidr,
            availability_zone=args.availability_zone,
            subnet_type=args.subnet_type,
            route_table_id=args.route_table_id
        )

        if success:
            print(f"Successfully created {args.subnet_type} subnet '{args.subnet_name}'")
            print(f"Subnet ID: {subnet_id}")
            print(f"CIDR: {args.subnet_cidr}")
            print(f"Availability Zone: {args.availability_zone}")
        else:
            print(f"Failed to create subnet '{args.subnet_name}'.")


class CreateRouteTableHandler(BaseVPCCommandHandler):
    """Handles creating a route table."""

    def execute(self, args: argparse.Namespace):
        """Execute route table creation."""
        success, route_table_id = create_route_table(
            ec2_client=self.client,
            vpc_id=args.vpc_id,
            route_table_name=args.route_table_name,
            igw_id=args.igw_id
        )

        if success:
            print(f"Successfully created route table '{args.route_table_name}'")
            print(f"Route Table ID: {route_table_id}")
            if args.igw_id:
                print(f"Internet route added via IGW: {args.igw_id}")
        else:
            print(f"Failed to create route table '{args.route_table_name}'.")
