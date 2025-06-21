import sys
from core.utils.tasks import BaseEC2Task
from tasks11.task1.handler import CreateBastionHostHandler, RollbackBastionHostHandler

class BastionHostTask(BaseEC2Task):
    @property
    def name(self) -> str:
        return "task11.1"

    @property
    def small_desc(self) -> str:
        return "Create and manage bastion host infrastructure with rollback capability."

    @property
    def usage(self) -> str:
        return f"""python {sys.argv[0]} {self.name} create [options]
            python {sys.argv[0]} {self.name} rollback [options]
                            
            Creates a complete bastion host infrastructure including:
            - VPC with public and private subnets
            - EC2 instance in public subnet (bastion host)
            - RDS instance in private subnets
            - Security groups with proper access rules
            - Internet Gateway and route tables

            Includes comprehensive rollback functionality to clean up resources."""

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='Bastion host operations'
        )

        create_parser = subparsers.add_parser(
            'create',
            help='Create complete bastion host infrastructure'
        )
        
        create_parser.add_argument(
            "--vpc-name",
            type=str,
            required=True,
            help="Name for the VPC and resource prefix."
        )
        
        create_parser.add_argument(
            "--vpc-cidr",
            type=str,
            default="10.0.0.0/16",
            help="CIDR block for the VPC (default: 10.0.0.0/16)."
        )
        
        create_parser.add_argument(
            "--key-pair-name",
            type=str,
            required=True,
            help="Name for the EC2 key pair."
        )
        
        create_parser.add_argument(
            "--ec2-instance-name",
            type=str,
            required=True,
            help="Name for the EC2 bastion instance."
        )
        
        create_parser.add_argument(
            "--db-name",
            type=str,
            default="bastiondb",
            help="Name for the RDS database (default: bastiondb)."
        )
        
        create_parser.add_argument(
            "--db-username",
            type=str,
            default="admin",
            help="Username for the RDS database (default: admin)."
        )
        
        create_parser.add_argument(
            "--db-password",
            type=str,
            required=True,
            help="Password for the RDS database."
        )
        
        create_parser.add_argument(
            "--allowed-ssh-ip",
            type=str,
            help="IP address allowed SSH access (default: auto-detect your IP)."
        )
        
        create_parser.add_argument(
            "--auto-rollback",
            action="store_true",
            help="Automatically rollback resources if creation fails."
        )
        
        create_parser.set_defaults(handler_class=CreateBastionHostHandler)

        rollback_parser = subparsers.add_parser(
            'rollback',
            help='Rollback bastion host infrastructure'
        )
        
        rollback_group = rollback_parser.add_mutually_exclusive_group()
        rollback_group.add_argument(
            "--vpc-name",
            type=str,
            help="Name of the VPC infrastructure to rollback."
        )
        
        rollback_group.add_argument(
            "--resource-file",
            type=str,
            help="Path to resource file for rollback."
        )
        
        rollback_parser.set_defaults(handler_class=RollbackBastionHostHandler)



