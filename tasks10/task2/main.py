import sys
from core.utils.tasks import BaseTask
from core.utils.rds.client import init_rds_client
from core.utils.dynamodb.client import init_dynamodb_client
from tasks10.task2.handler import RDSManagementHandler

class RDSManagementTask(BaseTask):
    @property
    def name(self) -> str:
        return "task10.2"

    @property
    def small_desc(self) -> str:
        return "Manage RDS instances and list DynamoDB tables."

    @property
    def usage(self) -> str:
        return f"""python {sys.argv[0]} {self.name} manage-rds [options]
                
                Available operations (use flags to select):
                --increase-storage    : Increase RDS instance storage by 25%
                --list-dynamodb      : List all DynamoDB tables in the region
                --create-snapshot    : Create manual snapshot of RDS instance
                
                You can combine any or all flags in a single command.
                
                Examples:
                  # Only increase storage
                  python {sys.argv[0]} {self.name} manage-rds --db-identifier my-db --increase-storage
                  
                  # Only list DynamoDB tables
                  python {sys.argv[0]} {self.name} manage-rds --db-identifier my-db --list-dynamodb
                  
                  # All operations
                  python {sys.argv[0]} {self.name} manage-rds --db-identifier my-db --increase-storage --list-dynamodb --create-snapshot"""

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='RDS management operations'
        )

        manage_parser = subparsers.add_parser(
            'manage-rds',
            help='Manage RDS instance with selective operations'
        )
        
        manage_parser.add_argument(
            "--db-identifier",
            type=str,
            required=False,
            help="RDS instance identifier to manage."
        )
        
        manage_parser.add_argument(
            "--increase-storage",
            action='store_true',
            help="Increase RDS instance storage by 25%."
        )

        
        manage_parser.add_argument(
            "--list-dynamodb",
            action='store_true',
            help="List all DynamoDB tables in the current region."
        )
        
        manage_parser.add_argument(
            "--create-snapshot",
            action='store_true',
            help="Create a manual snapshot (artificial backup) of the RDS instance."
        )
        
        manage_parser.set_defaults(handler_class=RDSManagementHandler)

    def run(self, args):
        """Runs the task with RDS and DynamoDB clients."""
        try:
            rds_client = init_rds_client()
            dynamodb_client = init_dynamodb_client()
            
            handler = args.handler_class(rds_client, dynamodb_client)
            handler.execute(args)
        except Exception as e:
            print(f"Error: {e}")
            return False
        
        return True
