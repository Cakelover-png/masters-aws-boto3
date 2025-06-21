import json
import logging
import os
import requests
from datetime import datetime
from botocore.exceptions import ClientError
from core.utils.rds.client import init_rds_client
from tasks8.utils.vpc import (
    create_vpc, create_internet_gateway, create_subnet, 
    create_route_table, get_availability_zones
)

class BastionHostManager:
    """Manages bastion host infrastructure creation and rollback."""
    
    def __init__(self, ec2_client):
        self.ec2_client = ec2_client
        self.rds_client = None
        self.created_resources = []
        self.rollback_file_path = "bastion_resources.json"
        
    def get_rds_client(self):
        """Lazy load RDS client."""
        if not self.rds_client:
            self.rds_client = init_rds_client()
        return self.rds_client
    
    def get_my_ip(self):
        """Get the public IP of the current machine."""
        try:
            response = requests.get('https://httpbin.org/ip', timeout=10)
            return response.json()['origin']
        except:  # noqa: E722
            logging.warning("Could not auto-detect IP, using 0.0.0.0/0")
            return "0.0.0.0/0"
    
    def add_resource_for_rollback(self, resource_type, resource_id, **kwargs):
        """Add a resource to the rollback list."""
        resource = {
            'type': resource_type,
            'id': resource_id,
            'created_at': datetime.now().isoformat(),
            **kwargs
        }
        self.created_resources.append(resource)
        logging.info(f"Added {resource_type} {resource_id} to rollback list")
    
    def create_key_pair(self, key_name):
        """Create EC2 key pair."""
        try:
            response = self.ec2_client.create_key_pair(KeyName=key_name)
            self.add_resource_for_rollback('key_pair', key_name)
            
            with open(f"{key_name}.pem", 'w') as f:
                f.write(response['KeyMaterial'])
            os.chmod(f"{key_name}.pem", 0o600)
            
            logging.info(f"Created key pair: {key_name}")
            return True, key_name
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
                logging.info(f"Key pair {key_name} already exists")
                return True, key_name
            logging.error(f"Error creating key pair: {e}")
            return False, None
    
    def create_security_group(self, vpc_id, sg_name, description):
        """Create security group."""
        try:
            response = self.ec2_client.create_security_group(
                GroupName=sg_name,
                Description=description,
                VpcId=vpc_id
            )
            sg_id = response['GroupId']
            self.add_resource_for_rollback('security_group', sg_id)
            
            self.ec2_client.create_tags(
                Resources=[sg_id],
                Tags=[{'Key': 'Name', 'Value': sg_name}]
            )
            
            logging.info(f"Created security group: {sg_id}")
            return True, sg_id
        except ClientError as e:
            logging.error(f"Error creating security group: {e}")
            return False, None
    
    def add_ssh_access_to_sg(self, sg_id, allowed_ip=None):
        """Add SSH access rule to security group."""
        try:
            if not allowed_ip:
                allowed_ip = self.get_my_ip()
            
            if not allowed_ip.endswith('/32') and not allowed_ip.endswith('/0'):
                allowed_ip += '/32'
            
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': allowed_ip}]
                    }
                ]
            )
            logging.info(f"Added SSH access from {allowed_ip} to security group {sg_id}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                logging.info("SSH rule already exists")
                return True
            logging.error(f"Error adding SSH access: {e}")
            return False
    
    def run_ec2_instance(self, sg_id, subnet_id, instance_name, key_name):
        """Launch EC2 instance."""
        try:
            response = self.ec2_client.run_instances(
                ImageId='ami-0c02fb55956c7d316',
                MinCount=1,
                MaxCount=1,
                InstanceType='t2.micro',
                KeyName=key_name,
                SecurityGroupIds=[sg_id],
                SubnetId=subnet_id,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [{'Key': 'Name', 'Value': instance_name}]
                    }
                ]
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            self.add_resource_for_rollback('ec2_instance', instance_id)
            
            logging.info(f"Launched EC2 instance: {instance_id}")
            return True, instance_id
        except ClientError as e:
            logging.error(f"Error launching EC2 instance: {e}")
            return False, None
    
    def create_db_subnet_group(self, group_name, vpc_id, subnet_ids):
        """Create RDS subnet group."""
        try:
            rds_client = self.get_rds_client()
            
            rds_client.create_db_subnet_group(
                DBSubnetGroupName=group_name,
                DBSubnetGroupDescription=f"Subnet group for {group_name}",
                SubnetIds=subnet_ids,
                Tags=[{'Key': 'Name', 'Value': group_name}]
            )
            
            self.add_resource_for_rollback('db_subnet_group', group_name)
            logging.info(f"Created DB subnet group: {group_name}")
            return True, group_name
        except ClientError as e:
            if e.response['Error']['Code'] == 'DBSubnetGroupAlreadyExistsFault':
                logging.info(f"DB subnet group {group_name} already exists")
                return True, group_name
            logging.error(f"Error creating DB subnet group: {e}")
            return False, None
    
    def create_rds_security_group(self, vpc_id, sg_name, ec2_sg_id):
        """Create RDS security group with access from EC2 security group."""
        try:
            success, rds_sg_id = self.create_security_group(vpc_id, sg_name, "RDS security group")
            if not success:
                return False, None
            
            self.ec2_client.authorize_security_group_ingress(
                GroupId=rds_sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 5432,
                        'ToPort': 5432,
                        'UserIdGroupPairs': [{'GroupId': ec2_sg_id}]
                    }
                ]
            )
            
            logging.info(f"Created RDS security group: {rds_sg_id}")
            return True, rds_sg_id
        except ClientError as e:
            logging.error(f"Error creating RDS security group: {e}")
            return False, None
    
    def create_db_instance(self, db_name, db_username, db_password, sg_id, subnet_group_name):
        """Create RDS instance."""
        try:
            rds_client = self.get_rds_client()
            
            response = rds_client.create_db_instance(
                DBInstanceIdentifier=f"{db_name}-instance",
                DBName=db_name,
                DBInstanceClass='db.t3.micro',
                Engine='postgres',
                MasterUsername=db_username,
                MasterUserPassword=db_password,
                AllocatedStorage=20,
                VpcSecurityGroupIds=[sg_id],
                DBSubnetGroupName=subnet_group_name,
                BackupRetentionPeriod=0,
                MultiAZ=False,
                PubliclyAccessible=False,
                StorageType='gp2',
                Tags=[
                    {'Key': 'Name', 'Value': db_name}
                ]
            )
            
            db_instance_id = response['DBInstance']['DBInstanceIdentifier']
            self.add_resource_for_rollback('rds_instance', db_instance_id)
            
            logging.info(f"Created RDS instance: {db_instance_id}")
            return True, db_instance_id
        except ClientError as e:
            logging.error(f"Error creating RDS instance: {e}")
            return False, None

    
    def create_bastion_infrastructure(self, vpc_name, vpc_cidr, key_pair_name, 
                                    ec2_instance_name, db_name, db_username, 
                                    db_password, allowed_ssh_ip=None):
        """Create complete bastion host infrastructure."""
        
        resources = {}
        
        try:
            azs = get_availability_zones(self.ec2_client)
            if len(azs) < 2:
                logging.error("Need at least 2 availability zones")
                return False, None
            
            success, vpc_id = create_vpc(self.ec2_client, vpc_name, vpc_cidr)
            if not success:
                return False, None
            self.add_resource_for_rollback('vpc', vpc_id)
            resources['vpc_id'] = vpc_id
            
            success, igw_id = create_internet_gateway(self.ec2_client, vpc_id, f"{vpc_name}-igw")
            if not success:
                return False, None
            self.add_resource_for_rollback('internet_gateway', igw_id, vpc_id=vpc_id)
            
            private_subnet_ids = []
            
            success, subnet_id = create_subnet(
                self.ec2_client, vpc_id, f"{vpc_name}-private-1", 
                "10.0.0.0/24", azs[0], 'private'
            )
            if not success:
                return False, None
            self.add_resource_for_rollback('subnet', subnet_id)
            private_subnet_ids.append(subnet_id)
            
            success, subnet_id = create_subnet(
                self.ec2_client, vpc_id, f"{vpc_name}-private-2", 
                "10.0.1.0/24", azs[1], 'private'
            )
            if not success:
                return False, None
            self.add_resource_for_rollback('subnet', subnet_id)
            private_subnet_ids.append(subnet_id)
            
            success, public_subnet_id = create_subnet(
                self.ec2_client, vpc_id, f"{vpc_name}-public-1", 
                "10.0.2.0/24", azs[0], 'public'
            )
            if not success:
                return False, None
            self.add_resource_for_rollback('subnet', public_subnet_id)
            
            success, public_rt_id = create_route_table(self.ec2_client, vpc_id, f"{vpc_name}-public-rt", igw_id)
            if not success:
                return False, None
            self.add_resource_for_rollback('route_table', public_rt_id)
            
            self.ec2_client.associate_route_table(SubnetId=public_subnet_id, RouteTableId=public_rt_id)
            
            self.ec2_client.modify_subnet_attribute(
                SubnetId=public_subnet_id,
                MapPublicIpOnLaunch={'Value': True}
            )
            
            success, key_name = self.create_key_pair(key_pair_name)
            if not success:
                return False, None
            resources['key_pair_name'] = key_name
            
            success, ec2_sg_id = self.create_security_group(
                vpc_id, f"{vpc_name}-ec2-sg", "Security group for bastion EC2"
            )
            if not success:
                return False, None
            
            success = self.add_ssh_access_to_sg(ec2_sg_id, allowed_ssh_ip)
            if not success:
                return False, None
            
            success, instance_id = self.run_ec2_instance(
                ec2_sg_id, public_subnet_id, ec2_instance_name, key_name
            )
            if not success:
                return False, None
            resources['ec2_instance_id'] = instance_id
            
            success, db_subnet_group = self.create_db_subnet_group(
                f"{vpc_name}-db-subnet-group", vpc_id, private_subnet_ids
            )
            if not success:
                return False, None
            
            success, rds_sg_id = self.create_rds_security_group(
                vpc_id, f"{vpc_name}-rds-sg", ec2_sg_id
            )
            if not success:
                return False, None
            
            success, db_instance_id = self.create_db_instance(
                db_name, db_username, db_password, rds_sg_id, db_subnet_group
            )
            if not success:
                return False, None
            resources['rds_instance_id'] = db_instance_id
            
            return True, resources
            
        except Exception as e:
            logging.error(f"Error in bastion infrastructure creation: {e}")
            return False, None
    
    def save_resources_for_rollback(self, resources, vpc_name):
        """Save created resources to file for later rollback."""
        try:
            rollback_data = {
                'vpc_name': vpc_name,
                'created_at': datetime.now().isoformat(),
                'resources': self.created_resources,
                'main_resources': resources
            }
            
            filename = f"{vpc_name}_rollback.json"
            with open(filename, 'w') as f:
                json.dump(rollback_data, f, indent=2)
            
            logging.info(f"Saved rollback data to {filename}")
        except Exception as e:
            logging.error(f"Error saving rollback data: {e}")
    
    def rollback_resource(self, resource):
        """Rollback a single resource."""
        try:
            resource_type = resource['type']
            resource_id = resource['id']
            
            if resource_type == 'rds_instance':
                rds_client = self.get_rds_client()
                rds_client.delete_db_instance(
                    DBInstanceIdentifier=resource_id,
                    SkipFinalSnapshot=True
                )
                logging.info(f"Deleted RDS instance: {resource_id}")
                
            elif resource_type == 'db_subnet_group':
                rds_client = self.get_rds_client()
                rds_client.delete_db_subnet_group(DBSubnetGroupName=resource_id)
                logging.info(f"Deleted DB subnet group: {resource_id}")
                
            elif resource_type == 'ec2_instance':
                self.ec2_client.terminate_instances(InstanceIds=[resource_id])
                logging.info(f"Terminated EC2 instance: {resource_id}")
                
            elif resource_type == 'security_group':
                self.ec2_client.delete_security_group(GroupId=resource_id)
                logging.info(f"Deleted security group: {resource_id}")
                
            elif resource_type == 'key_pair':
                self.ec2_client.delete_key_pair(KeyName=resource_id)
                try:
                    os.remove(f"{resource_id}.pem")
                except:  # noqa: E722
                    pass
                logging.info(f"Deleted key pair: {resource_id}")
                
            elif resource_type == 'route_table':
                self.ec2_client.delete_route_table(RouteTableId=resource_id)
                logging.info(f"Deleted route table: {resource_id}")
                
            elif resource_type == 'subnet':
                self.ec2_client.delete_subnet(SubnetId=resource_id)
                logging.info(f"Deleted subnet: {resource_id}")
                
            elif resource_type == 'internet_gateway':
                vpc_id = resource.get('vpc_id')
                if vpc_id:
                    self.ec2_client.detach_internet_gateway(
                        InternetGatewayId=resource_id, VpcId=vpc_id
                    )
                self.ec2_client.delete_internet_gateway(InternetGatewayId=resource_id)
                logging.info(f"Deleted internet gateway: {resource_id}")
                
            elif resource_type == 'vpc':
                self.ec2_client.delete_vpc(VpcId=resource_id)
                logging.info(f"Deleted VPC: {resource_id}")
                
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['InvalidGroupId.NotFound', 'InvalidVpcID.NotFound', 
                             'InvalidSubnetID.NotFound', 'InvalidRouteTableID.NotFound']:
                logging.info(f"Resource {resource_id} already deleted")
                return True
            logging.error(f"Error deleting {resource_type} {resource_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"Error deleting {resource_type} {resource_id}: {e}")
            return False
    
    def rollback_resources(self):
        """Rollback all created resources in reverse order."""
        for resource in reversed(self.created_resources):
            self.rollback_resource(resource)
        
        self.created_resources.clear()
    
    def rollback_from_file(self, filename):
        """Rollback resources from a saved file."""
        try:
            with open(filename, 'r') as f:
                rollback_data = json.load(f)
            
            resources = rollback_data.get('resources', [])
            
            for resource in reversed(resources):
                self.rollback_resource(resource)
            
            os.remove(filename)
            logging.info(f"Removed rollback file: {filename}")
            
            return True
        except Exception as e:
            logging.error(f"Error during rollback from file: {e}")
            return False
    
    def rollback_by_name(self, vpc_name):
        """Rollback resources by VPC name."""
        filename = f"{vpc_name}_rollback.json"
        if os.path.exists(filename):
            return self.rollback_from_file(filename)
        else:
            logging.error(f"Rollback file {filename} not found")
            return False
    
    def interactive_rollback(self):
        """Interactive rollback - show available rollback files."""
        rollback_files = [f for f in os.listdir('.') if f.endswith('_rollback.json')]
        
        if not rollback_files:
            print("No rollback files found.")
            return True
        
        print("Available rollback files:")
        for i, filename in enumerate(rollback_files, 1):
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    vpc_name = data.get('vpc_name', 'Unknown')
                    created_at = data.get('created_at', 'Unknown')
                print(f"{i}. {filename} (VPC: {vpc_name}, Created: {created_at})")
            except:  # noqa: E722
                print(f"{i}. {filename} (corrupted file)")
        
        try:
            choice = input("Enter file number to rollback (or 'all' for all files): ").strip()
            
            if choice.lower() == 'all':
                for filename in rollback_files:
                    self.rollback_from_file(filename)
                return True
            else:
                file_index = int(choice) - 1
                if 0 <= file_index < len(rollback_files):
                    return self.rollback_from_file(rollback_files[file_index])
                else:
                    print("Invalid choice.")
                    return False
                    
        except (ValueError, KeyboardInterrupt):
            print("Rollback cancelled.")
            return False
