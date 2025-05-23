import sys
from core.utils.tasks import BaseEC2Task
from tasks7.task1.handler import (CreateCompleteVPCHandler, CreateIGWHandler,
                                   CreateRouteTableHandler, CreateSubnetHandler, CreateVPCHandler)

class VPCTask(BaseEC2Task):
    @property
    def name(self) -> str:
        return "task7.1"

    @property
    def small_desc(self) -> str:
        return "VPC operations - create complete setup or individual components."

    @property
    def usage(self) -> str:
        return f"""python {sys.argv[0]} {self.name} <command> [options]
                Commands:
                create-complete    Create complete VPC with subnets, IGW, and route tables
                create-vpc         Create just a VPC
                create-igw         Create and attach Internet Gateway
                create-subnet      Create a subnet
                create-route-table Create a route table"""

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='VPC operations'
        )

        complete_parser = subparsers.add_parser(
            'create-complete',
            help='Creates a complete VPC with public/private subnets, IGW, and route tables'
        )
        complete_parser.add_argument(
            "--vpc-name",
            type=str,
            required=True,
            help="Name for the VPC (will be used as a tag)."
        )
        complete_parser.add_argument(
            "--vpc-cidr",
            type=str,
            required=True,
            help="CIDR block for the VPC (e.g., 10.0.0.0/16)."
        )
        complete_parser.add_argument(
            "--public-subnet-cidr",
            type=str,
            required=True,
            help="CIDR block for the public subnet (e.g., 10.0.1.0/24)."
        )
        complete_parser.add_argument(
            "--private-subnet-cidr",
            type=str,
            required=True,
            help="CIDR block for the private subnet (e.g., 10.0.2.0/24)."
        )
        complete_parser.add_argument(
            "--availability-zone",
            type=str,
            required=True,
            help="Availability zone for the subnets (e.g., us-west-2a)."
        )
        complete_parser.set_defaults(handler_class=CreateCompleteVPCHandler)

        vpc_parser = subparsers.add_parser('create-vpc', help='Create just a VPC')
        vpc_parser.add_argument(
            "--vpc-name",
            type=str,
            required=True,
            help="Name for the VPC."
        )
        vpc_parser.add_argument(
            "--vpc-cidr",
            type=str,
            required=True,
            help="CIDR block for the VPC (e.g., 10.0.0.0/16)."
        )
        vpc_parser.set_defaults(handler_class=CreateVPCHandler)

        igw_parser = subparsers.add_parser('create-igw', help='Create and attach Internet Gateway')
        igw_parser.add_argument(
            "--vpc-id",
            type=str,
            required=True,
            help="VPC ID to attach the Internet Gateway to."
        )
        igw_parser.add_argument(
            "--igw-name",
            type=str,
            required=True,
            help="Name for the Internet Gateway."
        )
        igw_parser.set_defaults(handler_class=CreateIGWHandler)

        subnet_parser = subparsers.add_parser('create-subnet', help='Create a subnet')
        subnet_parser.add_argument(
            "--vpc-id",
            type=str,
            required=True,
            help="VPC ID to create the subnet in."
        )
        subnet_parser.add_argument(
            "--subnet-name",
            type=str,
            required=True,
            help="Name for the subnet."
        )
        subnet_parser.add_argument(
            "--subnet-cidr",
            type=str,
            required=True,
            help="CIDR block for the subnet (e.g., 10.0.1.0/24)."
        )
        subnet_parser.add_argument(
            "--availability-zone",
            type=str,
            required=True,
            help="Availability zone for the subnet."
        )
        subnet_parser.add_argument(
            "--subnet-type",
            type=str,
            choices=['public', 'private'],
            required=True,
            help="Type of subnet (public or private)."
        )
        subnet_parser.add_argument(
            "--route-table-id",
            type=str,
            help="Optional: Route table ID to associate with the subnet."
        )
        subnet_parser.set_defaults(handler_class=CreateSubnetHandler)

        rt_parser = subparsers.add_parser('create-route-table', help='Create a route table')
        rt_parser.add_argument(
            "--vpc-id",
            type=str,
            required=True,
            help="VPC ID to create the route table in."
        )
        rt_parser.add_argument(
            "--route-table-name",
            type=str,
            required=True,
            help="Name for the route table."
        )
        rt_parser.add_argument(
            "--igw-id",
            type=str,
            help="Optional: Internet Gateway ID to create a route to (for public route tables)."
        )
        rt_parser.set_defaults(handler_class=CreateRouteTableHandler)
