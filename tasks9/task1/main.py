import sys
from core.utils.tasks import BaseEC2Task
from tasks9.task1.handler import LaunchEC2InstanceHandler

class EC2LaunchTask(BaseEC2Task):
    @property
    def name(self) -> str:
        return "task9.1"

    @property
    def small_desc(self) -> str:
        return "Create security group, key pair, and launch EC2 instance."

    @property
    def usage(self) -> str:
        return f"""python {sys.argv[0]} {self.name} launch-instance [options]
                
                Creates a security group with HTTP (0.0.0.0/0) and SSH (current IP) access,
                creates a key pair, and launches a t2.micro EC2 instance with:
                - 10GB gp2 storage
                - Public IP assignment
                - Amazon Linux 2 AMI"""

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='EC2 instance operations'
        )

        launch_parser = subparsers.add_parser(
            'launch-instance',
            help='Creates security group, key pair, and launches EC2 instance'
        )
        
        launch_parser.add_argument(
            "--vpc-id",
            type=str,
            required=True,
            help="VPC ID where the instance will be launched."
        )
        
        launch_parser.add_argument(
            "--subnet-id",
            type=str,
            required=True,
            help="Subnet ID where the instance will be launched (should be public)."
        )
        
        launch_parser.add_argument(
            "--key-name",
            type=str,
            help="Name for the key pair (if not specified, will be auto-generated)."
        )
        
        launch_parser.set_defaults(handler_class=LaunchEC2InstanceHandler)
