import argparse
from botocore.exceptions import ClientError

class CreateRDSInstanceHandler:
    """Handles creating an RDS instance with MySQL engine."""

    def __init__(self, rds_client, ec2_client):
        self.rds_client = rds_client
        self.ec2_client = ec2_client


    
    def execute(self, args: argparse.Namespace):
        """Execute the RDS instance creation process."""
        
        success = self._update_security_group(args.security_group_id)
        if not success:
            print(f"Failed to update security group {args.security_group_id}")
            return

        success, db_info = self._create_rds_instance(args)
        
        if success:
            print(f"Successfully created RDS instance '{args.db_identifier}'")
            print(f"DB Instance Identifier: {db_info['db_identifier']}")
            print(f"Engine: {db_info['engine']}")
            print(f"Storage: {db_info['storage']} GB")
            print(f"Security Group: {args.security_group_id}")
            print("\nWaiting for instance to become available...")
            
            if self._wait_for_db_available(args.db_identifier):
                self._print_connection_params(args.db_identifier)
        else:
            print(f"Failed to create RDS instance '{args.db_identifier}'")

    def _update_security_group(self, security_group_id):
        """Update security group to allow MySQL access from any IP."""
        try:
            response = self.ec2_client.describe_security_groups(GroupIds=[security_group_id])
            sg = response['SecurityGroups'][0]
            
            mysql_rule_exists = False
            for rule in sg['IpPermissions']:
                if (rule.get('FromPort') == 3306 and 
                    rule.get('ToPort') == 3306 and 
                    rule.get('IpProtocol') == 'tcp'):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            mysql_rule_exists = True
                            break
                    if mysql_rule_exists:
                        break
            
            if not mysql_rule_exists:
                self.ec2_client.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 3306,
                            'ToPort': 3306,
                            'IpRanges': [
                                {
                                    'CidrIp': '0.0.0.0/0',
                                    'Description': 'MySQL access from anywhere'
                                }
                            ]
                        }
                    ]
                )
                print(f"Added MySQL access rule to security group {security_group_id}")
            else:
                print(f"MySQL access rule already exists in security group {security_group_id}")
            
            return True
            
        except ClientError as e:
            print(f"Error updating security group: {e}")
            return False

    def _create_rds_instance(self, args):
        """Create the RDS instance with MySQL engine."""
        try:
            response = self.rds_client.create_db_instance(
                DBName='testdb',
                DBInstanceIdentifier=args.db_identifier,
                AllocatedStorage=60,
                DBInstanceClass='db.t3.micro',
                Engine='mysql',
                MasterUsername='admin',
                MasterUserPassword=args.master_password,
                VpcSecurityGroupIds=[args.security_group_id],
                BackupRetentionPeriod=7,
                Port=3306,
                MultiAZ=False,
                EngineVersion='8.0.35',
                AutoMinorVersionUpgrade=True,
                PubliclyAccessible=True,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': args.db_identifier
                    },
                ],
                StorageType='gp2',
                DeletionProtection=False,
            )
            
            db_info = {
                'db_identifier': response['DBInstance']['DBInstanceIdentifier'],
                'engine': response['DBInstance']['Engine'],
                'storage': response['DBInstance']['AllocatedStorage']
            }
            
            return True, db_info
            
        except ClientError as e:
            print(f"Error creating RDS instance: {e}")
            return False, None

    def _wait_for_db_available(self, db_identifier, max_wait_time=900):
        """Wait for the DB instance to become available."""
        try:
            waiter = self.rds_client.get_waiter('db_instance_available')
            waiter.wait(
                DBInstanceIdentifier=db_identifier,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': max_wait_time // 30
                }
            )
            print("RDS instance is now available!")
            return True
        except Exception as e:
            print(f"Error waiting for RDS instance: {e}")
            return False

    def _print_connection_params(self, db_identifier):
        """Print connection parameters for the RDS instance."""
        try:
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=db_identifier)
            instance = response['DBInstances'][0]
            endpoint = instance['Endpoint']
            
            print("\n=== Connection Parameters ===")
            print(f"Host: {endpoint['Address']}")
            print(f"Port: {endpoint['Port']}")
            print(f"Username: {instance['MasterUsername']}")
            print(f"Database: {instance['DBName']}")
            print(f"Engine: {instance['Engine']} {instance['EngineVersion']}")
            print("\nUse these parameters to connect with DBeaver, DataGrip, or any MySQL client.")
            
        except ClientError as e:
            print(f"Error getting connection parameters: {e}")
