import json
import os
import mimetypes
import logging
import random
from botocore.exceptions import ClientError
import requests
import datetime


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
    
    

def get_quote(author=None):
    """
    Fetches a random quote or quotes by a specific author from the quotes API.
    
    Args:
        author (str, optional): Name of the author to filter quotes by
    
    Returns:
        tuple: (success (bool), quote_data (dict or list))
    """
    try:
        base_url = "https://api.quotable.kurokeita.dev/api/quotes"
        
        if author:
            response = requests.get(f"{base_url}", params={"author": author}, timeout=10)
        else:
            response = requests.get(f"{base_url}/random", timeout=10)
        
        response.raise_for_status()
        
        quote_data = response.json()
        return True, quote_data
    
    except requests.RequestException as e:
        logging.error(f"Error fetching quote: {e}")
        return False, None
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing quote data: {e}")
        return False, None
    except Exception as e:
        logging.error(f"Unexpected error fetching quote: {e}")
        return False, None

def save_quote_to_s3(s3_client, quote_data, bucket_name, author=None):
    """
    Saves quote data as a JSON file to an S3 bucket.
    
    Args:
        s3_client: Initialized boto3 S3 client
        quote_data (dict or list): Quote data to save
        bucket_name (str): Name of the S3 bucket
    
    Returns:
        tuple: (success (bool), s3_key (str))
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        author = 'random' if not author else author
        filename = f"quote_{author}_{timestamp}.json"
        quote_json = json.dumps(quote_data, indent=2)
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=quote_json,
            ContentType='application/json'
        )
        
        return True, filename

    except Exception as e:
        logging.error(f"Error saving quote to S3: {e}")
        return False, None
