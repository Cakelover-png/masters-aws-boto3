from collections import defaultdict
import logging
from typing import Any, Dict, List, Optional
import os
from botocore.exceptions import ClientError
import math

from core.settings import PART_MIN_SIZE

def upload_small_file(s3_client, bucket_name: str, file_path: str, object_key: str):
    """
    Uploads a small file to S3 using the standard upload_file method.

    Args:
        s3_client: Initialized boto3 S3 client.
        bucket_name: Name of the target S3 bucket.
        file_path: The local path to the file to upload.
        object_key: The desired key (path) for the object in S3.
    """
    print(f"Attempting to upload small file: {file_path} to s3://{bucket_name}/{object_key}")
    try:
        s3_client.upload_file(file_path, bucket_name, object_key)
        print(f"Successfully uploaded {file_path} to s3://{bucket_name}/{object_key}")
        return True
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return False
    except ClientError as e:
        print(f"Error uploading file {file_path}: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during small file upload: {e}")
        return False

def upload_large_file(
    s3_client,
    bucket_name: str,
    file_path: str,
    object_key: str,
    use_standard_method: bool = False,
):
    """
    Uploads a large file to S3, with options for standard vs manual multipart upload
    and MIME type validation.

    Args:
        s3_client: Initialized boto3 S3 client.
        bucket_name: Name of the target S3 bucket.
        file_path: The local path to the file to upload.
        object_key: The desired key (path) for the object in S3.
        use_standard_method: If True, use s3_client.upload_file (handles multipart automatically).
                             If False (default), perform manual multipart upload.
    """
    print(f"Attempting to upload large file: {file_path} to s3://{bucket_name}/{object_key}")

    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} was not found.")
        return False
    # try:
    #     detected_mimetype = magic.from_file(file_path, mime=True)
    #     print(f"Detected MIME type: {detected_mimetype}")
    #     if detected_mimetype not in ALLOWED_MIMETYPE_EXTENSIONS:
    #         print(f"Error: File MIME type '{detected_mimetype}' is not in the allowed list: {ALLOWED_MIMETYPE_EXTENSIONS.keys()}")
    #         return False
    #     print("MIME type validation passed.")
    # except Exception as e:
    #     print(f"Error during MIME type detection for {file_path}: {e}")
    #     return False

    if use_standard_method:
        print("Using standard s3_client.upload_file method (handles multipart automatically)...")
        try:
            s3_client.upload_file(file_path, bucket_name, object_key)
            print(f"Successfully uploaded {file_path} to s3://{bucket_name}/{object_key} using standard method.")
            return True
        except ClientError as e:
            print(f"Error uploading file {file_path} using standard method: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during standard upload: {e}")
            return False
    else:
        print("Using manual multipart upload method...")
        upload_id = None
        part_size = PART_MIN_SIZE
        try:
            mpu = s3_client.create_multipart_upload(Bucket=bucket_name, Key=object_key)
            upload_id = mpu['UploadId']
            print(f"Multipart upload initiated. Upload ID: {upload_id}")

            parts = []
            part_number = 1
            file_size = os.path.getsize(file_path)
            total_parts = math.ceil(file_size / part_size)
            print(f"File size: {file_size} bytes. Part size: {part_size} bytes. Total parts: {total_parts}")

            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(part_size)
                    if not data:
                        break

                    print(f"Uploading Part {part_number}/{total_parts}...")
                    response = s3_client.upload_part(
                        Bucket=bucket_name,
                        Key=object_key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=data
                    )
                    parts.append({
                        'PartNumber': part_number,
                        'ETag': response['ETag']
                    })
                    print(f"Part {part_number} uploaded. ETag: {response['ETag']}")
                    part_number += 1

            print("Completing multipart upload...")
            result = s3_client.complete_multipart_upload(
                Bucket=bucket_name,
                Key=object_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            print(f"Successfully uploaded {file_path} to {result.get('Location', f's3://{bucket_name}/{object_key}')} using manual multipart.")
            return True

        except ClientError as e:
            print(f"Error during manual multipart upload for {file_path}: {e}")
            if upload_id:
                try:
                    print(f"Aborting multipart upload {upload_id} due to error...")
                    s3_client.abort_multipart_upload(
                        Bucket=bucket_name,
                        Key=object_key,
                        UploadId=upload_id
                    )
                    print("Multipart upload aborted.")
                except ClientError as abort_e:
                    print(f"Could not abort multipart upload {upload_id}: {abort_e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during manual multipart upload: {e}")
            if upload_id:
                 try:
                    print(f"Aborting multipart upload {upload_id} due to unexpected error...")
                    s3_client.abort_multipart_upload(
                        Bucket=bucket_name,
                        Key=object_key,
                        UploadId=upload_id
                    )
                    print("Multipart upload aborted.")
                 except ClientError as abort_e:
                    print(f"Could not abort multipart upload {upload_id}: {abort_e}")
            return False


def set_delete_lifecycle_policy(s3_client, bucket_name: str, days_to_expiration: int = 120):
    """
    Sets a lifecycle policy on an S3 bucket to delete objects after a specified number of days.
    This policy applies to all objects in the bucket.

    Args:
        s3_client: Initialized boto3 S3 client.
        bucket_name: Name of the target S3 bucket.
        days_to_expiration: Number of days after object creation when it should be deleted.
                            Defaults to 120.
    """
    policy_id = f'delete-after-{days_to_expiration}-days'
    print(f"Attempting to set lifecycle policy '{policy_id}' on bucket '{bucket_name}'...")

    lifecycle_config = {
        'Rules': [
            {
                'ID': policy_id,
                'Filter': {},
                'Status': 'Enabled',
                'Expiration': {
                    'Days': days_to_expiration
                },
            }
        ]
    }

    try:
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_config
        )
        print(f"Successfully set lifecycle policy '{policy_id}' on bucket '{bucket_name}'.")
        print(f"Objects older than {days_to_expiration} days will now be automatically deleted.")
        return True
    except ClientError as e:
        print(f"Error setting lifecycle policy on bucket {bucket_name}: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred setting lifecycle policy: {e}")
        return False
    




def delete_s3_object(s3_client, bucket_name: str, object_key: str):
    """
    Deletes a specific object from an S3 bucket.

    Args:
        s3_client: Initialized boto3 S3 client.
        bucket_name: Name of the bucket containing the object.
        object_key: The key (path/filename) of the object to delete.

    Returns:
        True if deletion was successful or the object didn't exist, False otherwise.
    """
    print(f"Attempting to delete object 's3://{bucket_name}/{object_key}'...")
    try:
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=object_key
        )
        print(f"Successfully deleted object 's3://{bucket_name}/{object_key}' (or it didn't exist).")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket_name}' not found.")
        else:
            print(f"Error deleting object 's3://{bucket_name}/{object_key}': {e}")
            logging.error(f"Failed to delete s3://{bucket_name}/{object_key}: {e}", exc_info=True)
        return False
    except Exception as e:
        print(f"An unexpected error occurred deleting object 's3://{bucket_name}/{object_key}': {e}")
        logging.exception(f"Unexpected error deleting s3://{bucket_name}/{object_key}: {e}")
        return False
    

def get_bucket_versioning_status(s3_client, bucket_name: str) -> Optional[str]:
    """
    Checks the versioning status of an S3 bucket.

    Args:
        s3_client: Initialized boto3 S3 client.
        bucket_name: Name of the bucket to check.

    Returns:
        A string indicating the status ('Enabled', 'Suspended', 'Not Enabled')
        or None if an error occurred.
    """
    print(f"Checking versioning status for bucket '{bucket_name}'...")
    try:
        response = s3_client.get_bucket_versioning(Bucket=bucket_name)
        status = response.get('Status', 'Not Enabled')
        print(f"Versioning status for bucket '{bucket_name}': {status}")
        return status
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket_name}' not found.")
        else:
            print(f"Error checking versioning for bucket '{bucket_name}': {e}")
            logging.error(f"ClientError getting versioning for {bucket_name}: {e}", exc_info=True)
        return None
    except Exception as e:
        print(f"An unexpected error occurred checking versioning for '{bucket_name}': {e}")
        logging.exception(f"Unexpected error getting versioning for {bucket_name}: {e}")
        return None

def list_object_versions(s3_client, bucket_name: str, object_key: str) -> Optional[List[Dict[str, Any]]]:
    """
    Lists all versions of a specific object in an S3 bucket.

    Args:
        s3_client: Initialized boto3 S3 client.
        bucket_name: Name of the bucket containing the object.
        object_key: The key (path/filename) of the object.

    Returns:
        A list of version dictionaries (containing 'VersionId', 'LastModified', 'IsLatest', 'Size')
        sorted by LastModified descending (newest first), or None if an error occurs or
        versioning is not enabled/object not found. Returns an empty list if the object exists
        but has no specific versions (e.g., versioning suspended or just created).
    """
    print(f"Listing versions for object 's3://{bucket_name}/{object_key}'...")
    versions_list = []
    try:
        paginator = s3_client.get_paginator('list_object_versions')
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=object_key)

        found_object = False
        for page in page_iterator:
            if 'Versions' in page:
                for version in page['Versions']:
                     if version['Key'] == object_key:
                        found_object = True
                        versions_list.append({
                            'VersionId': version.get('VersionId', 'null'),
                            'LastModified': version['LastModified'],
                            'IsLatest': version['IsLatest'],
                            'Size': version.get('Size', 0)
                        })
            if 'DeleteMarkers' in page:
                 for marker in page['DeleteMarkers']:
                      if marker['Key'] == object_key:
                         found_object = True
                         versions_list.append({
                             'VersionId': marker.get('VersionId'),
                             'LastModified': marker['LastModified'],
                             'IsLatest': marker['IsLatest'],
                             'Size': 0,
                             'Type': 'DeleteMarker'
                         })

        if not found_object:
             print(f"Object 's3://{bucket_name}/{object_key}' not found or has no versions/markers.")
             try:
                 s3_client.head_object(Bucket=bucket_name, Key=object_key)
                 print(f"Object 's3://{bucket_name}/{object_key}' exists but has no tracked versions/markers (versioning might be suspended?).")
             except ClientError as head_error:
                 if head_error.response['Error']['Code'] == '404':
                      print(f"Object 's3://{bucket_name}/{object_key}' not found.")
                 else:
                      raise head_error
             return []

        versions_list.sort(key=lambda x: x['LastModified'], reverse=True)

        print(f"Found {len(versions_list)} version(s)/marker(s) for 's3://{bucket_name}/{object_key}'.")
        return versions_list

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket_name}' not found.")
        else:
            print(f"Error listing versions for 's3://{bucket_name}/{object_key}': {e}")
            logging.error(f"ClientError listing versions for {bucket_name}/{object_key}: {e}", exc_info=True)
        return None
    except Exception as e:
        print(f"An unexpected error occurred listing versions for 's3://{bucket_name}/{object_key}': {e}")
        logging.exception(f"Unexpected error listing versions for {bucket_name}/{object_key}: {e}")
        return None


def restore_previous_version(s3_client, bucket_name: str, object_key: str) -> bool:
    """
    Restores the second most recent version of an object to become the current version.

    This works by copying the second most recent version over the current key,
    which creates a new version identical to the desired previous one. The actual
    previous version remains in the history.

    Args:
        s3_client: Initialized boto3 S3 client.
        bucket_name: Name of the bucket containing the object.
        object_key: The key (path/filename) of the object.

    Returns:
        True if the restoration (copy) was successful, False otherwise.
    """
    print(f"Attempting to restore previous version for 's3://{bucket_name}/{object_key}'...")

    versions = list_object_versions(s3_client, bucket_name, object_key)

    if versions is None:
        print("Error: Could not retrieve versions to determine previous version.")
        return False

    actual_versions = [v for v in versions if v.get('Type') != 'DeleteMarker' and v.get('VersionId') != 'null']

    if len(actual_versions) < 2:
        print(f"Error: Cannot restore previous version. Found {len(actual_versions)} actual version(s) (excluding delete markers and null IDs). At least two are required.")
        return False

    previous_version_info = actual_versions[1]
    previous_version_id = previous_version_info['VersionId']

    print(f"Identified previous version to restore: VersionId='{previous_version_id}', LastModified='{previous_version_info['LastModified']}'")

    try:
        copy_source = {
            'Bucket': bucket_name,
            'Key': object_key,
            'VersionId': previous_version_id
        }
        print(f"Executing copy operation: Source={copy_source}, Destination=s3://{bucket_name}/{object_key}")
        s3_client.copy_object(
            Bucket=bucket_name,
            Key=object_key,
            CopySource=copy_source,
        )
        print(f"Successfully restored version '{previous_version_id}'. It is now the latest version of 's3://{bucket_name}/{object_key}'.")
        return True
    except ClientError as e:
        print(f"Error restoring previous version for 's3://{bucket_name}/{object_key}': {e}")
        logging.error(f"ClientError restoring version {previous_version_id} for {bucket_name}/{object_key}: {e}", exc_info=True)
        return False
    except Exception as e:
        print(f"An unexpected error occurred restoring previous version for 's3://{bucket_name}/{object_key}': {e}")
        logging.exception(f"Unexpected error restoring version {previous_version_id} for {bucket_name}/{object_key}: {e}")
        return False

def organize_objects_by_extension(s3_client, bucket_name: str) -> Optional[Dict[str, int]]:
    """
    Organizes objects in the root of an S3 bucket into folders named by their extension.

    Args:
        s3_client: Initialized boto3 S3 client.
        bucket_name: Name of the bucket to organize.

    Returns:
        A dictionary containing the count of files moved per extension (e.g., {'jpg': 2, 'csv': 5}),
        or None if a major error occurred (like bucket not found). Errors moving individual
        files are logged but do not cause a total failure.
    """
    print(f"Starting organization process for bucket '{bucket_name}'...")
    extension_counts = defaultdict(int)
    processed_count = 0
    moved_count = 0
    skipped_count = 0
    error_count = 0

    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name, Delimiter='/')
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    object_key = obj['Key']
                    processed_count += 1
                    if '/' in object_key or obj.get('Size', 0) == 0:
                         skipped_count +=1
                         continue

                    try:
                        _, extension = os.path.splitext(object_key)
                        extension = extension.lower().strip('.') # Normalize: lowercase, remove dot
                    except Exception as e:
                        print(f"Warning: Could not extract extension for key '{object_key}': {e}")
                        logging.warning(f"Extension extraction failed for {bucket_name}/{object_key}", exc_info=True)
                        error_count += 1
                        continue

                    if not extension:
                        print(f"Skipping '{object_key}' (no extension found).")
                        skipped_count += 1
                        continue

                    new_key = f"{extension}/{object_key}"

                    print(f"Attempting to move '{object_key}' to '{new_key}'...")
                    try:
                        copy_source = {'Bucket': bucket_name, 'Key': object_key}
                        s3_client.copy_object(
                            CopySource=copy_source,
                            Bucket=bucket_name,
                            Key=new_key
                        )
                        logging.info(f"Successfully copied {bucket_name}/{object_key} to {bucket_name}/{new_key}")

                        try:
                            s3_client.delete_object(Bucket=bucket_name, Key=object_key)
                            logging.info(f"Successfully deleted original object {bucket_name}/{object_key}")
                            extension_counts[extension] += 1
                            moved_count += 1
                            print(f"Successfully moved '{object_key}' to '{new_key}'.")
                        except ClientError as delete_err:
                             print(f"Error: Copied '{object_key}' to '{new_key}' but failed to delete original: {delete_err}")
                             logging.error(f"Failed deleting original {bucket_name}/{object_key} after copy: {delete_err}", exc_info=True)
                             error_count += 1

                    except ClientError as move_err:
                        print(f"Error: Failed to move '{object_key}': {move_err}")
                        logging.error(f"Failed moving {bucket_name}/{object_key}: {move_err}", exc_info=True)
                        error_count += 1
                    except Exception as unexpected_err:
                        print(f"Error: An unexpected error occurred moving '{object_key}': {unexpected_err}")
                        logging.exception(f"Unexpected error moving {bucket_name}/{object_key}")
                        error_count += 1

        print("\n--- Summary ---")
        print(f"Total objects scanned (at root): {processed_count}")
        print(f"Objects successfully moved:     {moved_count}")
        print(f"Objects skipped (in folder/no ext): {skipped_count}")
        print(f"Errors during move:           {error_count}")
        print("----------------------------")

        return dict(extension_counts)

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket_name}' not found.")
        else:
            print(f"Error listing objects in bucket '{bucket_name}': {e}")
            logging.error(f"ClientError organizing bucket {bucket_name}: {e}", exc_info=True)
        return None
    except Exception as e:
        print(f"An unexpected error occurred during the organization process for '{bucket_name}': {e}")
        logging.exception(f"Unexpected error organizing bucket {bucket_name}")
        return None