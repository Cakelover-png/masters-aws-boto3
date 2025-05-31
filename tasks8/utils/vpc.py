import ipaddress
import logging
from botocore.exceptions import ClientError

def validate_cidr(cidr_block):
    """Validates a CIDR block format."""
    try:
        ipaddress.IPv4Network(cidr_block, strict=True)
        return True
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError):
        return False

def validate_subnet_in_vpc(vpc_cidr, subnet_cidr):
    """Validates that a subnet CIDR is within the VPC CIDR range."""
    try:
        vpc_network = ipaddress.IPv4Network(vpc_cidr)
        subnet_network = ipaddress.IPv4Network(subnet_cidr)
        return subnet_network.subnet_of(vpc_network)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError):
        return False

def get_vpc_cidr(ec2_client, vpc_id):
    """Gets the CIDR block of a VPC."""
    try:
        response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
        return response['Vpcs'][0]['CidrBlock'] if response['Vpcs'] else None
    except ClientError:
        return None

def get_availability_zones(ec2_client):
    """Gets list of available availability zones in the region."""
    try:
        response = ec2_client.describe_availability_zones(
            Filters=[{'Name': 'state', 'Values': ['available']}]
        )
        return [az['ZoneName'] for az in response['AvailabilityZones']]
    except ClientError as e:
        logging.error(f"Error getting availability zones: {e}")
        return []

def generate_subnet_cidrs(vpc_cidr, num_subnets):
    """
    Generates CIDR blocks for subnets within a VPC.
    Returns a list of CIDR blocks for public subnets followed by private subnets.
    """
    try:
        vpc_network = ipaddress.IPv4Network(vpc_cidr)
        total_subnets_needed = num_subnets * 2
        
        subnet_prefix_length = vpc_network.prefixlen
        
        while True:
            subnet_prefix_length += 1
            if subnet_prefix_length > 30:
                raise ValueError("Not enough address space for the requested number of subnets")
            
            available_subnets = 2 ** (subnet_prefix_length - vpc_network.prefixlen)
            if available_subnets >= total_subnets_needed:
                break
        
        subnets = list(vpc_network.subnets(new_prefix=subnet_prefix_length))
        
        if len(subnets) < total_subnets_needed:
            raise ValueError(f"Cannot fit {total_subnets_needed} subnets in VPC CIDR {vpc_cidr}")
        
        public_cidrs = [str(subnets[i]) for i in range(num_subnets)]
        private_cidrs = [str(subnets[i + num_subnets]) for i in range(num_subnets)]
        
        return public_cidrs, private_cidrs
        
    except Exception as e:
        logging.error(f"Error generating subnet CIDRs: {e}")
        return None, None

def create_vpc(ec2_client, vpc_name, vpc_cidr):
    """Creates a VPC with the specified CIDR block."""
    if not validate_cidr(vpc_cidr):
        logging.error(f"Invalid VPC CIDR block: {vpc_cidr}")
        return False, None
    
    try:
        vpc_response = ec2_client.create_vpc(CidrBlock=vpc_cidr)
        vpc_id = vpc_response['Vpc']['VpcId']
        
        ec2_client.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': vpc_name}])
        ec2_client.get_waiter('vpc_available').wait(VpcIds=[vpc_id])
        
        logging.info(f"Created VPC {vpc_id} with CIDR {vpc_cidr}")
        return True, vpc_id
    except (ClientError, Exception) as e:
        logging.error(f"Error creating VPC: {e}")
        return False, None

def create_internet_gateway(ec2_client, vpc_id, igw_name):
    """Creates an Internet Gateway and attaches it to a VPC."""
    try:
        igw_response = ec2_client.create_internet_gateway()
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        
        ec2_client.create_tags(Resources=[igw_id], Tags=[{'Key': 'Name', 'Value': igw_name}])
        ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        
        logging.info(f"Created and attached Internet Gateway {igw_id}")
        return True, igw_id
    except (ClientError, Exception) as e:
        logging.error(f"Error creating Internet Gateway: {e}")
        return False, None

def create_subnet(ec2_client, vpc_id, subnet_name, subnet_cidr, availability_zone, 
                 subnet_type, route_table_id=None):
    """Creates a subnet in the specified VPC."""
    if not validate_cidr(subnet_cidr):
        logging.error(f"Invalid subnet CIDR block: {subnet_cidr}")
        return False, None
    
    vpc_cidr = get_vpc_cidr(ec2_client, vpc_id)
    if vpc_cidr and not validate_subnet_in_vpc(vpc_cidr, subnet_cidr):
        logging.error(f"Subnet CIDR {subnet_cidr} is not within VPC CIDR {vpc_cidr}")
        return False, None
    
    try:
        subnet_response = ec2_client.create_subnet(
            VpcId=vpc_id,
            CidrBlock=subnet_cidr,
            AvailabilityZone=availability_zone
        )
        subnet_id = subnet_response['Subnet']['SubnetId']
        
        ec2_client.create_tags(
            Resources=[subnet_id],
            Tags=[
                {'Key': 'Name', 'Value': subnet_name},
                {'Key': 'Type', 'Value': subnet_type}
            ]
        )
        
        if subnet_type == 'public':
            ec2_client.modify_subnet_attribute(
                SubnetId=subnet_id,
                MapPublicIpOnLaunch={'Value': True}
            )
        
        if route_table_id:
            ec2_client.associate_route_table(SubnetId=subnet_id, RouteTableId=route_table_id)
        
        logging.info(f"Created {subnet_type} subnet {subnet_id} with CIDR {subnet_cidr}")
        return True, subnet_id
    except (ClientError, Exception) as e:
        logging.error(f"Error creating subnet: {e}")
        return False, None

def create_route_table(ec2_client, vpc_id, route_table_name, igw_id=None):
    """Creates a route table in the specified VPC."""
    try:
        route_table_response = ec2_client.create_route_table(VpcId=vpc_id)
        route_table_id = route_table_response['RouteTable']['RouteTableId']
        
        ec2_client.create_tags(Resources=[route_table_id], Tags=[{'Key': 'Name', 'Value': route_table_name}])
        
        if igw_id:
            ec2_client.create_route(
                RouteTableId=route_table_id,
                DestinationCidrBlock='0.0.0.0/0',
                GatewayId=igw_id
            )
            logging.info(f"Added internet route to route table {route_table_id}")
        
        logging.info(f"Created route table {route_table_id}")
        return True, route_table_id
    except (ClientError, Exception) as e:
        logging.error(f"Error creating route table: {e}")
        return False, None

def create_vpc_with_multiple_subnets(ec2_client, vpc_name, vpc_cidr, num_subnets, 
                                   availability_zones=None):
    """
    Creates a complete VPC setup with N public and N private subnets.
    
    Key differences between public and private subnets:
    - Public subnets: Have a route to Internet Gateway (0.0.0.0/0 -> IGW)
    - Private subnets: Only have local VPC routes, no direct internet access
    - Public subnets: Auto-assign public IP addresses to instances
    - Private subnets: Do not auto-assign public IP addresses
    """
    
    if not validate_cidr(vpc_cidr):
        logging.error(f"Invalid VPC CIDR block: {vpc_cidr}")
        return False, None
    
    if num_subnets > 200:
        logging.error("Maximum number of subnets is limited to 200")
        return False, None
    
    if num_subnets < 1:
        logging.error("Number of subnets must be at least 1")
        return False, None
    
    try:
        if not availability_zones:
            availability_zones = get_availability_zones(ec2_client)
            if not availability_zones:
                logging.error("No availability zones available")
                return False, None
        
        public_cidrs, private_cidrs = generate_subnet_cidrs(vpc_cidr, num_subnets)
        if not public_cidrs or not private_cidrs:
            logging.error("Failed to generate subnet CIDRs")
            return False, None
        
        success, vpc_id = create_vpc(ec2_client, vpc_name, vpc_cidr)
        if not success:
            return False, None
        
        success, igw_id = create_internet_gateway(ec2_client, vpc_id, f"{vpc_name}-igw")
        if not success:
            return False, None
        
        success, public_rt_id = create_route_table(ec2_client, vpc_id, f"{vpc_name}-public-rt", igw_id)
        if not success:
            return False, None
        
        success, private_rt_id = create_route_table(ec2_client, vpc_id, f"{vpc_name}-private-rt")
        if not success:
            return False, None
        
        public_subnet_ids = []
        for i in range(num_subnets):
            az = availability_zones[i % len(availability_zones)]
            subnet_name = f"{vpc_name}-public-subnet-{i+1}"
            
            success, subnet_id = create_subnet(
                ec2_client, vpc_id, subnet_name, public_cidrs[i], 
                az, 'public', public_rt_id
            )
            if not success:
                return False, None
            public_subnet_ids.append(subnet_id)
        
        private_subnet_ids = []
        for i in range(num_subnets):
            az = availability_zones[i % len(availability_zones)]
            subnet_name = f"{vpc_name}-private-subnet-{i+1}"
            
            success, subnet_id = create_subnet(
                ec2_client, vpc_id, subnet_name, private_cidrs[i], 
                az, 'private', private_rt_id
            )
            if not success:
                return False, None
            private_subnet_ids.append(subnet_id)
        
        return True, {
            'vpc_id': vpc_id,
            'igw_id': igw_id,
            'public_subnet_ids': public_subnet_ids,
            'private_subnet_ids': private_subnet_ids,
            'public_route_table_id': public_rt_id,
            'private_route_table_id': private_rt_id
        }
    
    except Exception as e:
        logging.error(f"Error in VPC creation with multiple subnets: {e}")
        return False, None
