import sys
from core.utils.rds.client import init_rds_client
from core.utils.vpc.client import init_ec2_client
from core.utils.tasks import BaseTask
from tasks10.task1.handler import CreateRDSInstanceHandler

class RDSTask(BaseTask):
    @property
    def name(self) -> str:
        return "task10.1"

    @property
    def small_desc(self) -> str:
        return "Create RDS MySQL instance with security group."

    @property
    def usage(self) -> str:
        return f"""python {sys.argv[0]} {self.name} create-rds [options]
                
                Creates an RDS MySQL instance with:
                - 60 GB storage
                - MySQL engine
                - Assigned to specified security group
                - Database port (3306) accessible from any IP address
                
                The security group will be updated to allow MySQL access from 0.0.0.0/0"""

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='RDS operations'
        )

        # Main command for creating RDS instance
        rds_parser = subparsers.add_parser(
            'create-rds',
            help='Creates an RDS MySQL instance with security group'
        )
        
        rds_parser.add_argument(
            "--db-identifier",
            type=str,
            required=True,
            help="Unique identifier for the RDS instance."
        )
        
        rds_parser.add_argument(
            "--security-group-id",
            type=str,
            required=True,
            help="Security group ID to assign to the RDS instance."
        )
        
        rds_parser.add_argument(
            "--master-password",
            type=str,
            required=True,
            help="Master password for the RDS instance (must be at least 8 characters)."
        )
        
        rds_parser.set_defaults(handler_class=CreateRDSInstanceHandler)

    def run(self, args):
        """Runs the task with RDS and EC2 clients."""
        try:
            rds_client = init_rds_client()
            ec2_client = init_ec2_client()
            
            handler = args.handler_class(rds_client, ec2_client)
            handler.execute(args)
        except Exception as e:
            print(f"Error: {e}")
            return False
        
        return True
