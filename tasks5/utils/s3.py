import os
import mimetypes
import logging
from botocore.exceptions import ClientError

def host_static_website(s3_client, bucket_name: str, source_folder: str, region: str = 'us-west-2'):
    """
    Creates an S3 bucket, uploads files from source folder,
    configures it for static website hosting, and sets public access.
    
    Args:
        s3_client: Initialized boto3 S3 client
        bucket_name (str): Name for the S3 bucket to create
        source_folder (str): Path to folder containing website files
    
    Returns:
        tuple: (success (bool), website_url (str))
    """
    if not os.path.isdir(source_folder):
        logging.error(f"Source folder '{source_folder}' does not exist or is not a directory")
        return False, None
    
    try:
        logging.info(f"Uploading files from {source_folder}...")
        for root, _, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, source_folder)
                s3_key = rel_path.replace('\\', '/')
                
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                try:
                    logging.info(f"Uploading: {rel_path}")
                    s3_client.upload_file(
                        file_path, 
                        bucket_name, 
                        s3_key,
                        ExtraArgs={'ContentType': content_type}
                    )
                except Exception as e:
                    logging.error(f"Error uploading {file_path}: {e}")
                    return False, None
        
        website_configuration = {
            'IndexDocument': {'Suffix': 'index.html'}
        }
        
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration=website_configuration
        )
        
        if region == 'us-east-1':
            website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
        else:
            website_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
        
        return True, website_url
    
    except ClientError as e:
        logging.error(f"AWS client error: {e}")
        return False, None
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return False, None
