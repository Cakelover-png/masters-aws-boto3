import sys
from core.utils.tasks import BaseEC2Task
from tasks8.task1.handler import CreateVPCWithMultipleSubnetsHandler

class VPCTask(BaseEC2Task):
    @property
    def name(self) -> str:
        return "task8.1"

    @property
    def small_desc(self) -> str:
        return "Create VPC with N public and N private subnets."

    @property
    def usage(self) -> str:
        return f"""python {sys.argv[0]} {self.name} create-vpc-with-subnets [options]
                
                Creates a complete VPC with N public and N private subnets.
                
                Key differences between subnet types:
                - Public subnets: Have route to Internet Gateway (0.0.0.0/0), auto-assign public IPs
                - Private subnets: No direct internet route, use local VPC routes only
                
                Maximum subnets: 200 (AWS default limit)"""

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='VPC operations with multiple subnets'
        )

        # Main command for creating VPC with multiple subnets
        vpc_parser = subparsers.add_parser(
            'create-vpc-with-subnets',
            help='Creates a VPC with N public and N private subnets'
        )
        
        vpc_parser.add_argument(
            "--vpc-name",
            type=str,
            required=True,
            help="Name for the VPC (will be used as a tag prefix)."
        )
        
        vpc_parser.add_argument(
            "--vpc-cidr",
            type=str,
            required=True,
            help="CIDR block for the VPC (e.g., 10.0.0.0/16)."
        )
        
        vpc_parser.add_argument(
            "-n", "--num-subnets",
            type=int,
            required=True,
            help="Number of public and private subnets to create (max 200)."
        )
        
        vpc_parser.add_argument(
            "--availability-zones",
            type=str,
            nargs='+',
            help="List of availability zones to use. If not specified, will use available AZs in the region."
        )
        
        vpc_parser.set_defaults(handler_class=CreateVPCWithMultipleSubnetsHandler)
