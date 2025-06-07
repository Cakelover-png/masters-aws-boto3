
import argparse
import requests
from core.utils.vpc.handlers import BaseVPCCommandHandler
from tasks9.utils.ec2 import create_security_group_and_launch_instance

class LaunchEC2InstanceHandler(BaseVPCCommandHandler):
    """Handles creating security group, key pair, and launching EC2 instance."""

    def execute(self, args: argparse.Namespace):
        """Execute the EC2 instance launch process."""
        
        try:
            current_ip = requests.get('https://ipinfo.io/ip', timeout=5).text.strip()
            print(f"Detected current public IP: {current_ip}")
        except Exception as e:
            print(f"Error getting current IP: {e}")
            return

        success, instance_info = create_security_group_and_launch_instance(
            ec2_client=self.client,
            vpc_id=args.vpc_id,
            subnet_id=args.subnet_id,
            current_ip=current_ip,
            key_name=args.key_name or f"key-{args.vpc_id[:8]}"
        )

        if success:
            print("Successfully created security group and launched EC2 instance")
            print(f"Instance ID: {instance_info['instance_id']}")
            print(f"Security Group ID: {instance_info['security_group_id']}")
            print(f"Key Pair Name: {instance_info['key_name']}")
            print(f"Public IP: {instance_info['public_ip']}")
            print(f"Instance State: {instance_info['state']}")
            
            print("\nTo connect via SSH:")
            print(f"ssh -i {instance_info['key_name']}.pem ec2-user@{instance_info['public_ip']}")
        else:
            print("Failed to create security group and launch EC2 instance.")
