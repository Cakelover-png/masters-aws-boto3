import argparse
from core.utils.vpc.handlers import BaseVPCCommandHandler
from tasks11.utils.bastion import BastionHostManager

class CreateBastionHostHandler(BaseVPCCommandHandler):
    """Handles creating a complete bastion host setup with VPC, EC2, and RDS."""

    def execute(self, args: argparse.Namespace):
        """Execute the bastion host creation process."""
        
        manager = BastionHostManager(self.client)
        
        try:
            success, resources = manager.create_bastion_infrastructure(
                vpc_name=args.vpc_name,
                vpc_cidr=args.vpc_cidr,
                key_pair_name=args.key_pair_name,
                ec2_instance_name=args.ec2_instance_name,
                db_name=args.db_name,
                db_username=args.db_username,
                db_password=args.db_password,
                allowed_ssh_ip=args.allowed_ssh_ip
            )

            if success:
                print("Successfully created bastion host infrastructure:")
                print(f"VPC ID: {resources.get('vpc_id')}")
                print(f"EC2 Instance ID: {resources.get('ec2_instance_id')}")
                print(f"RDS Instance ID: {resources.get('rds_instance_id')}")
                print(f"Key Pair: {resources.get('key_pair_name')}")
                
                manager.save_resources_for_rollback(resources, args.vpc_name)
            else:
                print("Failed to create bastion host infrastructure.")
                if args.auto_rollback:
                    print("Performing automatic rollback...")
                    manager.rollback_resources()
        except Exception as e:
            print(f"Error during creation: {e}")
            if args.auto_rollback:
                print("Performing automatic rollback...")
                manager.rollback_resources()

class RollbackBastionHostHandler(BaseVPCCommandHandler):
    """Handles rollback of bastion host resources."""

    def execute(self, args: argparse.Namespace):
        """Execute rollback of bastion host resources."""
        
        manager = BastionHostManager(self.client)
        
        try:
            if args.vpc_name:
                success = manager.rollback_by_name(args.vpc_name)
            elif args.resource_file:
                success = manager.rollback_from_file(args.resource_file)
            else:
                success = manager.interactive_rollback()
            
            if success:
                print("Successfully rolled back resources.")
            else:
                print("Rollback completed with some errors. Check logs for details.")
                
        except Exception as e:
            print(f"Error during rollback: {e}")
