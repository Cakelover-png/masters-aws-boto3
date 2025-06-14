import logging
from os import getenv
import boto3
from botocore.exceptions import ClientError

def init_rds_client():
    """Initializes and returns a boto3 RDS client."""
    try:
        required_vars = ["aws_access_key_id", "aws_secret_access_key", "aws_region_name"]
        missing_vars = [var for var in required_vars if not getenv(var)]
        if missing_vars:
            logging.warning(f"Missing environment variables: {', '.join(missing_vars)}. Relying on other credential sources (e.g., IAM role, config file).")
        
        client = boto3.client(
            "rds",
            aws_access_key_id=getenv("aws_access_key_id"),
            aws_secret_access_key=getenv("aws_secret_access_key"),
            aws_session_token=getenv("aws_session_token"),
            region_name=getenv("aws_region_name"),
        )
        
        client.describe_db_instances()
        logging.info(f"Successfully initialized RDS client for region '{getenv('aws_region_name')}'.")
        return client

    except ClientError as e:
        logging.error(f"AWS ClientError initializing RDS client: {e}")
        if e.response['Error']['Code'] == 'InvalidClientTokenId' or e.response['Error']['Code'] == 'SignatureDoesNotMatch':
            logging.error("AWS credentials (key, secret, or token) may be invalid or expired.")
        elif e.response['Error']['Code'] == 'UnauthorizedOperation':
            logging.error("AWS credentials are valid but lack permissions for RDS operations.")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred initializing RDS client: {e}")
        raise
