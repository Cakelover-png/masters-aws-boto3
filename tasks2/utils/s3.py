import logging
import json
from typing import Optional, Dict, Any, List

import magic
import requests
from botocore.exceptions import ClientError

from core.settings import ALLOWED_MIMETYPE_EXTENSIONS



def list_buckets(s3_client) -> List[Dict[str, Any]]:
    try:
        response = s3_client.list_buckets()
        logging.info(f"Found {len(response.get('Buckets', []))} buckets.")
        return response.get('Buckets', [])
    except ClientError as e:
        logging.error(f"Could not list buckets: {e}", exc_info=True)
        raise

def bucket_exists(s3_client, bucket_name: str) -> bool:
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logging.debug(f"Bucket '{bucket_name}' exists and is accessible.")
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "404":
            logging.debug(f"Bucket '{bucket_name}' does not exist.")
            return False
        elif error_code == "403":
            logging.warning(f"Access denied to bucket '{bucket_name}'. Cannot confirm existence.")
            return False
        else:
            logging.error(f"Error checking bucket '{bucket_name}': {e}", exc_info=True)
            raise

def create_bucket(s3_client, bucket_name: str, region: str = 'us-west-2') -> None:

    try:
        if region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
            logging.info(f"Bucket '{bucket_name}' created successfully in region 'us-east-1'.")
        else:
            location = {'LocationConstraint': region}
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration=location
            )
            logging.info(f"Bucket '{bucket_name}' created successfully in region '{region}'.")
    except ClientError as e:
        logging.error(f"Could not create bucket '{bucket_name}' in region '{region}': {e}", exc_info=True)
        raise


def delete_bucket(s3_client, bucket_name: str) -> None:
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
        logging.info(f"Bucket '{bucket_name}' deleted successfully.")
    except ClientError as e:
        logging.error(f"Could not delete bucket '{bucket_name}': {e}", exc_info=True)
        if e.response['Error']['Code'] == 'BucketNotEmpty':
            logging.error(f"Bucket '{bucket_name}' is not empty. Please delete objects first.")
        raise


def download_file_and_upload_to_s3(s3_client,
                                   bucket_name: str,
                                   url: str,
                                   s3_key: str,) -> None:
    logging.info(f"Executing command: upload (Bucket: {bucket_name}, URL: {url}, Key: {s3_key})")
    try:
        detected_mime = None
        try:
            logging.debug(f"Fetching initial chunk from {url} for type detection.")
            with requests.get(url, stream=True, timeout=15) as r_head:
                r_head.raise_for_status()
                initial_chunk = r_head.raw.read(2048)
                if not initial_chunk:
                        raise ValueError("Downloaded file appears empty.")
                detected_mime = magic.from_buffer(initial_chunk, mime=True)
                logging.info(f"Detected MIME type: {detected_mime}")

                if detected_mime not in set(ALLOWED_MIMETYPE_EXTENSIONS.keys()):
                    allowed_str = ", ".join(ALLOWED_MIMETYPE_EXTENSIONS.get(m, m) for m in ALLOWED_MIMETYPE_EXTENSIONS)
                    raise ValueError(f"Invalid file type detected: '{detected_mime}'. Allowed types: {allowed_str}")
        except requests.exceptions.RequestException as req_err:
            raise ValueError(f"Failed to download initial part of file: {req_err}") from req_err
        except ImportError:
            logging.error("python-magic library not found. Cannot perform file type validation.")
            
            raise
        except Exception as magic_err:
                
                logging.warning(f"Error during MIME type detection: {magic_err}. Proceeding without reliable type.", exc_info=True)
                raise ValueError(f"Could not determine file type: {magic_err}") from magic_err

        print(f"Validation determined type {detected_mime}. Proceeding with upload...")
        with requests.get(url, stream=True, timeout=600) as response: 
            response.raise_for_status()

            extra_args = {}
            
            if detected_mime:
                    extra_args['ContentType'] = detected_mime

            s3_client.upload_fileobj(
                Fileobj=response.raw,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args
            )
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            print(f"Successfully uploaded '{url}' to 's3://{bucket_name}/{s3_key}'")
            print(f"File accessible at: {s3_url}")


    except (ClientError, ValueError, requests.exceptions.RequestException) as e:
        logging.error(f"Failed to upload file: {e}", exc_info=True)
        print(f"Error uploading file for key '{s3_key}'. See logs.")
    except Exception as e:
        logging.exception(f"Unexpected error during upload: {e}")
        print("An unexpected error occurred during upload. See logs.")


def set_object_acl(s3_client, bucket_name: str, s3_key: str, acl: str = 'private') -> None:
    valid_acls = [
        'private', 'public-read', 'public-read-write', 'authenticated-read',
        'aws-exec-read', 'bucket-owner-read', 'bucket-owner-full-control'
    ]
    if acl not in valid_acls:
         raise ValueError(f"Invalid ACL '{acl}'. Must be one of {valid_acls}")

    try:
        s3_client.put_object_acl(ACL=acl, Bucket=bucket_name, Key=s3_key)
        logging.info(f"Set ACL '{acl}' for object 's3://{bucket_name}/{s3_key}'.")
    except ClientError as e:
        logging.error(f"Could not set ACL for 's3://{bucket_name}/{s3_key}': {e}", exc_info=True)
        raise


def generate_public_read_policy(bucket_name: str) -> str:
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject"],
            "Resource": f"arn:aws:s3:::{bucket_name}/*"
        }]
    }
    return json.dumps(policy)


def apply_bucket_policy(s3_client, bucket_name: str, policy_json: str) -> None:
    try:
        # Validate JSON structure before sending to AWS (optional but good practice)
        json.loads(policy_json)
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policy_json)
        logging.info(f"Successfully applied bucket policy to '{bucket_name}'.")
    except json.JSONDecodeError as e:
         logging.error(f"Invalid JSON provided for bucket policy: {e}", exc_info=True)
         raise
    except ClientError as e:
        logging.error(f"Could not apply policy to bucket '{bucket_name}': {e}", exc_info=True)
        raise


def delete_public_access_block(s3_client, bucket_name: str) -> None:
    try:
        s3_client.delete_public_access_block(Bucket=bucket_name)
        logging.info(f"Deleted Public Access Block for bucket '{bucket_name}'.")
    except ClientError as e:
        logging.error(f"Could not delete Public Access Block for '{bucket_name}': {e}", exc_info=True)
        raise


def read_bucket_policy(s3_client, bucket_name: str) -> Optional[str]:
    try:
        policy_response = s3_client.get_bucket_policy(Bucket=bucket_name)
        policy_str = policy_response.get("Policy")
        if policy_str:
             logging.debug(f"Retrieved policy for bucket '{bucket_name}'.")
             return policy_str
        else:
             logging.warning(f"get_bucket_policy succeeded for '{bucket_name}' but response contained no 'Policy' key.")
             return None
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
            logging.info(f"Bucket '{bucket_name}' does not have a policy attached.")
            return None
        else:
            logging.error(f"Could not read policy for bucket '{bucket_name}': {e}", exc_info=True)
            raise