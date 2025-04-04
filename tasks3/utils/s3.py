import magic
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
    validate_mimetype: bool = False,
    allowed_mimetypes: list = None,
    part_size_mb: int = 10
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
        validate_mimetype: If True, validate the file's MIME type before uploading.
        allowed_mimetypes: A list of allowed MIME types (e.g., ['image/jpeg', 'application/pdf'])
                           Required if validate_mimetype is True.
        part_size_mb: The size of each part in MB for manual multipart upload (min 5MB).
    """
    print(f"Attempting to upload large file: {file_path} to s3://{bucket_name}/{object_key}")

    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} was not found.")
        return False

    if validate_mimetype:
        if not allowed_mimetypes:
            print("Error: MIME type validation requested, but allowed_mimetypes list is empty or None.")
            return False
        try:
            detected_mimetype = magic.from_file(file_path, mime=True)
            print(f"Detected MIME type: {detected_mimetype}")
            if detected_mimetype not in allowed_mimetypes:
                print(f"Error: File MIME type '{detected_mimetype}' is not in the allowed list: {allowed_mimetypes}")
                return False
            print("MIME type validation passed.")
        except Exception as e:
            print(f"Error during MIME type detection for {file_path}: {e}")
            return False

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
        part_size = part_size_mb * 1024 * 1024
        if part_size < PART_MIN_SIZE:
             print(f"Warning: Specified part size {part_size_mb}MB is less than the minimum 5MB. Using 5MB.")
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