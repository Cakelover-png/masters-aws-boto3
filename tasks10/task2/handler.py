import argparse
from datetime import datetime
from botocore.exceptions import ClientError

class RDSManagementHandler:
    """Handles RDS instance management and DynamoDB table listing."""

    def __init__(self, rds_client, dynamodb_client):
        self.rds_client = rds_client
        self.dynamodb_client = dynamodb_client

    def execute(self, args: argparse.Namespace):
        """Execute selected RDS management operations."""
        
        operations_performed = 0
        
        if args.increase_storage:
            print("=== Increasing RDS Storage by 25% ===")
            if self._increase_rds_storage(args.db_identifier):
                operations_performed += 1
            print()
        
        if args.list_dynamodb:
            print("=== Listing DynamoDB Tables ===")
            self._list_dynamodb_tables()
            operations_performed += 1
            print()
        
        if args.create_snapshot:
            print("=== Creating Manual Snapshot ===")
            if self._create_manual_snapshot(args.db_identifier):
                operations_performed += 1
            print()
        
        if operations_performed == 0:
            print("No operations were requested. Use --help to see available options.")
        else:
            print(f"Completed {operations_performed} operation(s).")


    def _increase_rds_storage(self, db_identifier):
        """Increase RDS instance storage by 25%."""
        try:
            print(f"Checking current RDS instance storage for '{db_identifier}'...")
            
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=db_identifier)
            instance = response['DBInstances'][0]
            current_storage = instance['AllocatedStorage']
            
            print(f"Current allocated storage: {current_storage} GB")
            
            increase_amount = int(current_storage * 0.25)
            new_storage = current_storage + increase_amount
            
            print(f"Increasing storage by {increase_amount} GB (25%)")
            print(f"New storage size will be: {new_storage} GB")
            
            self.rds_client.modify_db_instance(
                DBInstanceIdentifier=db_identifier,
                AllocatedStorage=new_storage,
                ApplyImmediately=True
            )
            
            print(f"Successfully initiated storage increase for RDS instance '{db_identifier}'")
            print("Note: The storage modification will take some time to complete.")
            return True
            
        except ClientError as e:
            print(f"Error increasing RDS storage: {e}")
            return False

    def _list_dynamodb_tables(self):
        """List all DynamoDB tables in the region."""
        try:
            paginator = self.dynamodb_client.get_paginator('list_tables')
            table_count = 0
            
            for page in paginator.paginate():
                for table_name in page.get('TableNames', []):
                    table_count += 1
                    print(f"{table_count}. {table_name}")
                    
                    try:
                        table_info = self.dynamodb_client.describe_table(TableName=table_name)
                        status = table_info['Table']['TableStatus']
                        item_count = table_info['Table'].get('ItemCount', 'Unknown')
                        table_size = table_info['Table'].get('TableSizeBytes', 0)
                        
                        size_mb = round(table_size / (1024 * 1024), 2) if table_size > 0 else 0
                        
                        print(f"   Status: {status}, Items: {item_count}, Size: {size_mb} MB")
                    except ClientError:
                        print("(Unable to get detailed info)")
            
            if table_count == 0:
                print("No DynamoDB tables found in this region.")
            else:
                print(f"Total tables found: {table_count}")
                
        except ClientError as e:
            print(f"Error listing DynamoDB tables: {e}")

    def _create_manual_snapshot(self, db_identifier):
        """Create a manual snapshot of the RDS instance."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            snapshot_id = f"{db_identifier}-manual-snapshot-{timestamp}"
            
            print(f"Creating manual snapshot for RDS instance '{db_identifier}'...")
            
            response = self.rds_client.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_id,
                DBInstanceIdentifier=db_identifier,
                Tags=[
                    {
                        'Key': 'Type',
                        'Value': 'Manual'
                    },
                    {
                        'Key': 'CreatedBy',
                        'Value': 'CLI-Tool'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Artificial-Backup'
                    }
                ]
            )
            
            print(f"Successfully initiated manual snapshot creation: {snapshot_id}")
            print("Note: The snapshot creation will take some time to complete.")
            print(f"Snapshot status: {response['DBSnapshot']['Status']}")
            
            return True
            
        except ClientError as e:
            print(f"Error creating manual snapshot: {e}")
            return False
