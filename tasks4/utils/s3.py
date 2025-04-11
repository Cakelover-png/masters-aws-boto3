from datetime import datetime, timezone
import magic
import boto3
import botocore
import os
import logging
from dateutil.relativedelta import relativedelta


def upload_file_by_type(s3_client: boto3.client, bucket_name: str, local_file_path: str) -> tuple[bool, str | None]:
    """
    Detects the MIME type of a local file using python-magic and uploads it
    to an S3 bucket under a folder named after the MIME type.

    Args:
        s3_client: Initialized Boto3 S3 client.
        bucket_name: The target S3 bucket name.
        local_file_path: The path to the local file to upload.

    Returns:
        A tuple containing:
        - bool: True if upload was successful, False otherwise.
        - str | None: The S3 key if successful, None otherwise.
    """
    if not os.path.isfile(local_file_path):
        logging.error(f"File not found: {local_file_path}")
        return False, None

    try:
        mime_type = magic.from_file(local_file_path, mime=True)
        logging.info(f"Detected MIME type for '{local_file_path}': {mime_type}")

        if not mime_type:
             logging.warning(f"Could not determine MIME type for {local_file_path}. Uploading to 'unknown/'.")
             mime_type = "unknown"

        file_name = os.path.basename(local_file_path)
        s3_key = f"{mime_type}/{file_name}"

        logging.info(f"Attempting to upload '{local_file_path}' to s3://{bucket_name}/{s3_key}")

        s3_client.upload_file(local_file_path, bucket_name, s3_key)

        logging.info(f"Successfully uploaded to s3://{bucket_name}/{s3_key}")
        return True, s3_key
    except magic.MagicException as e:
        logging.error(f"Error detecting file type for {local_file_path}: {e}")
        return False, None
    except botocore.exceptions.ClientError as e:
        logging.error(f"AWS S3 Client Error during upload: {e}")
        return False, None
    except FileNotFoundError:
        logging.error(f"File not found during upload process: {local_file_path}")
        return False, None
    except Exception as e:
        logging.error(f"An unexpected error occurred during upload: {e}")
        return False, None
    


def simple_delete_old_versions(s3_client: boto3.client, bucket_name: str, object_keys: list[str]) -> int:
    """
    Deletes object versions older than exactly 6 months for the specified keys.
    This version is simplified and less verbose than the previous example.

    Args:
        s3_client: Initialized Boto3 S3 client.
        bucket_name: The target S3 bucket name.
        object_keys: A list of S3 object keys to check.

    Returns:
        The total count of versions queued for deletion. Returns -1 on major error during deletion.
        Note: This count reflects attempted deletions; check logs for specific errors.
    """
    if not object_keys:
        logging.warning("No object keys provided.")
        return 0

    cutoff_date = datetime.now(timezone.utc) - relativedelta(months=6)
    logging.info(f"Deleting versions older than {cutoff_date.isoformat()} for {len(object_keys)} key(s).")

    versions_to_delete = []

    for key in object_keys:
        try:
            paginator = s3_client.get_paginator('list_object_versions')
            page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=key)

            for page in page_iterator:
                for version_info in page.get('Versions', []) + page.get('DeleteMarkers', []):
                    if version_info.get('Key') == key:
                        last_modified = version_info.get('LastModified')
                        version_id = version_info.get('VersionId')
                        is_latest = version_info.get('IsLatest', False)

                        if version_id and last_modified and not is_latest and last_modified < cutoff_date:
                            logging.debug(f"  Queueing {key} - VersionId: {version_id}")
                            versions_to_delete.append({'Key': key, 'VersionId': version_id})

        except botocore.exceptions.ClientError as e:
            logging.error(f"Error listing versions for key '{key}': {e}. Skipping.")
            continue
        except Exception as e:
            logging.error(f"Unexpected error processing key '{key}': {e}. Skipping.", exc_info=True)
            continue
    if not versions_to_delete:
        logging.info("No object versions found matching the criteria.")
        return 0

    logging.info(f"Attempting to delete {len(versions_to_delete)} version(s).")
    try:
        delete_payload = {'Objects': versions_to_delete}
        response = s3_client.delete_objects(Bucket=bucket_name, Delete=delete_payload)

        deleted_count = len(versions_to_delete)
        if 'Errors' in response and response['Errors']:
            failed_count = len(response['Errors'])
            deleted_count -= failed_count
            logging.error(f"Bulk delete completed with {failed_count} errors:")
            for error in response['Errors']:
                logging.error(f"  - Failed Key: {error.get('Key')}, VersionId: {error.get('VersionId')}, Code: {error.get('Code')}, Message: {error.get('Message')}")
            return deleted_count
        else:
            logging.info(f"Successfully submitted deletion request for {deleted_count} versions.")
            return deleted_count

    except botocore.exceptions.ClientError as e:
        logging.error(f"CRITICAL ERROR during S3 delete_objects call: {e}")
        return -1
    except Exception as e:
        logging.error(f"CRITICAL UNEXPECTED ERROR during S3 delete_objects call: {e}", exc_info=True)
        return -1
    



def setup_static_website(s3_client: boto3.client, bucket_name: str, first_name: str, last_name: str) -> tuple[bool, str | None]:
    """
    Creates a simple index.html, uploads it, and configures S3 static website hosting.

    Args:
        s3_client: Initialized Boto3 S3 client.
        bucket_name: The target S3 bucket name.
        first_name: User's first name for the HTML content.
        last_name: User's last name for the HTML content.

    Returns:
        A tuple containing:
        - bool: True if setup was successful, False otherwise.
        - str | None: The website URL if successful, None otherwise.
    """
    index_key = 'index.html'
    error_key = 'error.html'

    html_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>Welcome!</title>
                <style>
                    body {{ font-family: sans-serif; text-align: center; padding-top: 50px; }}
                    h1 {{ color: #333; }}
                </style>
            </head>
            <body>
                <h1>Hello, {first_name} {last_name}!</h1>
                <p>This page is hosted on Amazon S3.</p>
            </body>
            </html>
    """

    try:
        logging.info(f"Uploading {index_key} to bucket '{bucket_name}'...")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=index_key,
            Body=html_content.encode('utf-8'),
            ContentType='text/html'
        )
        logging.info(f"Successfully uploaded {index_key}.")

        logging.info(f"Configuring static website hosting for bucket '{bucket_name}'...")
        website_configuration = {
            'ErrorDocument': {'Key': error_key},
            'IndexDocument': {'Suffix': index_key},
        }
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration=website_configuration
        )

        location_response = s3_client.get_bucket_location(Bucket=bucket_name)
        region = location_response.get('LocationConstraint') or 'us-east-1'

        if region == 'us-east-1':
             website_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
        else:
             website_url = f"http://{bucket_name}.s3-website.{region}.amazonaws.com"

        logging.info(f"Static website setup complete. URL: {website_url}")
        return True, website_url
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        logging.error(f"AWS S3 Client Error during website setup (Code: {error_code}): {e}")
        return False, None
    except Exception as e:
        logging.error(f"An unexpected error occurred during website setup: {e}", exc_info=True)
        return False, None


