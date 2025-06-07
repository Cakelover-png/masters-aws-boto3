import logging
import requests
from botocore.exceptions import ClientError

def get_current_public_ip():
    """Gets the current public IP address."""
    try:
        response = requests.get('https://ipinfo.io/ip', timeout=5)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error getting current IP: {e}")
        return None

def get_amazon_linux_ami(ec2_client):
    """Gets the latest Amazon Linux 2 AMI ID."""
    try:
        response = ec2_client.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['amzn2-ami-hvm-*']},
                {'Name': 'architecture', 'Values': ['x86_64']},
                {'Name': 'virtualization-type', 'Values': ['hvm']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        
        images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
        if images:
            return images[0]['ImageId']
        return None
    except ClientError as e:
        logging.error(f"Error getting Amazon Linux AMI: {e}")
        return None

def create_security_group(ec2_client, vpc_id, group_name, current_ip):
    """Creates a security group with HTTP and SSH access."""
    try:
        response = ec2_client.create_security_group(
            GroupName=group_name,
            Description='Security group for web server with SSH access',
            VpcId=vpc_id
        )
        sg_id = response['GroupId']
        
        ec2_client.create_tags(
            Resources=[sg_id],
            Tags=[{'Key': 'Name', 'Value': group_name}]
        )
        
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP access'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': f'{current_ip}/32', 'Description': 'SSH access'}]
                }
            ]
        )
        
        logging.info(f"Created security group {sg_id} with HTTP and SSH rules")
        return True, sg_id
    except ClientError as e:
        logging.error(f"Error creating security group: {e}")
        return False, None

def create_key_pair(ec2_client, key_name):
    """Creates a key pair and saves the private key."""
    try:
        try:
            ec2_client.describe_key_pairs(KeyNames=[key_name])
            logging.info(f"Key pair {key_name} already exists")
            return True, key_name
        except ClientError:
            pass
        
        response = ec2_client.create_key_pair(KeyName=key_name)
        private_key = response['KeyMaterial']
        
        with open(f"{key_name}.pem", 'w') as f:
            f.write(private_key)
        
        import os
        os.chmod(f"{key_name}.pem", 0o400)
        
        logging.info(f"Created key pair {key_name} and saved to {key_name}.pem")
        return True, key_name
    except ClientError as e:
        logging.error(f"Error creating key pair: {e}")
        return False, None

def launch_ec2_instance(ec2_client, ami_id, subnet_id, security_group_id, key_name):
    """Launches an EC2 instance with specified parameters."""
    try:
        response = ec2_client.run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro',
            KeyName=key_name,
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'SubnetId': subnet_id,
                    'Groups': [security_group_id],
                    'AssociatePublicIpAddress': True
                }
            ],
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'VolumeSize': 10,
                        'VolumeType': 'gp2',
                        'DeleteOnTermination': True
                    }
                }
            ]
        )
        
        instance_id = response['Instances'][0]['InstanceId']
        
        ec2_client.create_tags(
            Resources=[instance_id],
            Tags=[{'Key': 'Name', 'Value': f'WebServer-{instance_id[:8]}'}]
        )
        
        print("Waiting for instance to be running...")
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        instances = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = instances['Reservations'][0]['Instances'][0]
        
        public_ip = instance.get('PublicIpAddress', 'None')
        state = instance['State']['Name']
        
        logging.info(f"Launched EC2 instance {instance_id} with public IP {public_ip}")
        return True, {
            'instance_id': instance_id,
            'public_ip': public_ip,
            'state': state
        }
    except ClientError as e:
        logging.error(f"Error launching EC2 instance: {e}")
        return False, None

def create_security_group_and_launch_instance(ec2_client, vpc_id, subnet_id, current_ip, key_name):
    """Creates security group, key pair, and launches EC2 instance."""
    try:
        ami_id = get_amazon_linux_ami(ec2_client)
        if not ami_id:
            logging.error("Could not find Amazon Linux 2 AMI")
            return False, None
        
        sg_name = f"web-server-sg-{vpc_id[:8]}"
        success, sg_id = create_security_group(ec2_client, vpc_id, sg_name, current_ip)
        if not success:
            return False, None
        
        success, key_name = create_key_pair(ec2_client, key_name)
        if not success:
            return False, None
        
        success, instance_info = launch_ec2_instance(ec2_client, ami_id, subnet_id, sg_id, key_name)
        if not success:
            return False, None
        
        if instance_info['public_ip'] != 'None':
            print(f"Testing SSH connectivity to {instance_info['public_ip']}...")
            print("Instance is ready for SSH connection (once you have the private key)")
        
        return True, {
            'instance_id': instance_info['instance_id'],
            'security_group_id': sg_id,
            'key_name': key_name,
            'public_ip': instance_info['public_ip'],
            'state': instance_info['state']
        }
        
    except Exception as e:
        logging.error(f"Error in create_security_group_and_launch_instance: {e}")
        return False, None
