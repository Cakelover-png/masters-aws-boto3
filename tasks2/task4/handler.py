import argparse
import json
import logging
from botocore.exceptions import ClientError
import requests

from core.utils.s3.handlers import BaseS3CommandHandler
from tasks2.utils.s3 import (
    apply_bucket_policy, bucket_exists, create_bucket, delete_bucket,
    delete_public_access_block, download_file_and_upload_to_s3, generate_public_read_policy,
    list_buckets, read_bucket_policy, set_object_acl
)

class ListBucketsHandler(BaseS3CommandHandler):
    def execute(self, args: argparse.Namespace):
        logging.info("Executing command: list")
        try:
            buckets = list_buckets(self.client)
            if buckets:
                print("Buckets:")
                for bucket in buckets:
                    print(f"- {bucket['Name']} (Created: {bucket['CreationDate']})")
            else:
                print("No buckets found or accessible.")
        except (ClientError, ValueError) as e:
            logging.error(f"Failed to list buckets: {e}", exc_info=True)
            print("Error listing buckets. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error listing buckets: {e}")
            print("An unexpected error occurred. See logs.")


class BucketExistsHandler(BaseS3CommandHandler):
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: exists (Bucket: {args.bucket_name})")
        try:
            if bucket_exists(self.client, args.bucket_name):
                print(f"Bucket '{args.bucket_name}' exists.")
            else:
                print(f"Bucket '{args.bucket_name}' does not exist or is inaccessible.")
        except (ClientError, ValueError) as e:
            logging.error(f"Failed to check bucket existence: {e}", exc_info=True)
            print(f"Error checking bucket '{args.bucket_name}'. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error checking bucket: {e}")
            print("An unexpected error occurred. See logs.")


class CreateBucketHandler(BaseS3CommandHandler):
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: create (Bucket: {args.bucket_name})")
        try:
            
            
            create_bucket(self.client, args.bucket_name)
            print(f"Bucket '{args.bucket_name}' created successfully.")
        except (ClientError, ValueError) as e:
            logging.error(f"Failed to create bucket: {e}", exc_info=True)
            print(f"Error creating bucket '{args.bucket_name}'. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error creating bucket: {e}")
            print("An unexpected error occurred. See logs.")


class DeleteBucketHandler(BaseS3CommandHandler):
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: delete (Bucket: {args.bucket_name})")
        try:
            if not bucket_exists(self.client, args.bucket_name):
                 print(f"Bucket '{args.bucket_name}' does not exist. Cannot delete.")
                 return

            print(f"Attempting to delete bucket '{args.bucket_name}' (ensure it's empty!)...")
            delete_bucket(self.client, args.bucket_name)
            print(f"Bucket '{args.bucket_name}' deleted successfully.")
        except ClientError as e:
            logging.error(f"Failed to delete bucket: {e}", exc_info=True)
            print(f"Error deleting bucket '{args.bucket_name}'.")
            if e.response.get("Error", {}).get("Code") == 'BucketNotEmpty':
                print("Hint: Bucket must be empty before deletion.")
            else:
                print("See logs for details.")
        except ValueError as e:
             logging.error(f"Failed to delete bucket due to config error: {e}", exc_info=True)
             print(f"Configuration error deleting bucket '{args.bucket_name}'. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error deleting bucket: {e}")
            print("An unexpected error occurred. See logs.")


class UploadObjectHandler(BaseS3CommandHandler):
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: upload (Bucket: {args.bucket_name}, URL: {args.url}, Key: {args.s3_key})")
        try:
            download_file_and_upload_to_s3(self.client, args.bucket_name, args.url, args.s3_key)
        except (ClientError, ValueError, requests.exceptions.RequestException) as e:
            logging.error(f"Failed to upload file: {e}", exc_info=True)
            print(f"Error uploading file for key '{args.s3_key}'. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error during upload: {e}")
            print("An unexpected error occurred during upload. See logs.")


class SetObjectAclHandler(BaseS3CommandHandler):
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: set-object-acl (Bucket: {args.bucket_name}, Key: {args.s3_key}, ACL: {args.acl})")
        try:
            set_object_acl(self.client, args.bucket_name, args.s3_key, args.acl)
            print(f"ACL '{args.acl}' set for 's3://{args.bucket_name}/{args.s3_key}'.")
        except (ClientError, ValueError) as e:
            logging.error(f"Failed to set object ACL: {e}", exc_info=True)
            print(f"Error setting ACL for object '{args.s3_key}'. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error setting object ACL: {e}")
            print("An unexpected error occurred. See logs.")


class GetBucketPolicyHandler(BaseS3CommandHandler):
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: get-policy (Bucket: {args.bucket_name})")
        try:
            policy = read_bucket_policy(self.client, args.bucket_name)
            if policy:
                print(f"Policy for bucket '{args.bucket_name}':")
                try:
                    print(json.dumps(json.loads(policy), indent=2))
                except json.JSONDecodeError:
                    logging.warning("Retrieved policy is not valid JSON. Printing raw.")
                    print(policy) 
            else:
                print(f"No policy found for bucket '{args.bucket_name}'.")
        except (ClientError, ValueError) as e:
            logging.error(f"Failed to get bucket policy: {e}", exc_info=True)
            print(f"Error getting policy for bucket '{args.bucket_name}'. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error getting bucket policy: {e}")
            print("An unexpected error occurred. See logs.")


class SetBucketPolicyHandler(BaseS3CommandHandler):
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: set-policy (Bucket: {args.bucket_name})")
        try:
            if not args.skip_pab_delete:
                print("Attempting to remove Public Access Block (required for public policy)...")
                try:
                    delete_public_access_block(self.client, args.bucket_name)
                    print("Public Access Block removed successfully.")
                except ClientError as pab_error:
                    
                    logging.warning(f"Could not delete Public Access Block (may not exist or perms issue): {pab_error}."
                                    "Continuing policy application attempt.", exc_info=True)
                    print("Warning: Could not remove Public Access Block. Policy might not be effective. See logs.")
            else:
                 print("Skipping Public Access Block removal as requested.")

            print("Generating and applying public read policy...")
            policy_json = generate_public_read_policy(args.bucket_name)
            apply_bucket_policy(self.client, args.bucket_name, policy_json)
            print(f"Successfully applied public read policy to '{args.bucket_name}'.")

        except (ClientError, ValueError) as e:
            logging.error(f"Failed to set bucket policy: {e}", exc_info=True)
            print(f"Error setting policy for bucket '{args.bucket_name}'. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error setting bucket policy: {e}")
            print("An unexpected error occurred. See logs.")


class DeletePublicAccessBlockHandler(BaseS3CommandHandler):
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: delete-pab (Bucket: {args.bucket_name})")
        try:
            delete_public_access_block(self.client, args.bucket_name)
            print(f"Public Access Block deleted successfully for '{args.bucket_name}'.")
        except ClientError as e:
             
             if e.response.get("Error", {}).get("Code") == 'NoSuchPublicAccessBlockConfiguration':
                 logging.warning(f"No public access block configuration found for bucket {args.bucket_name}. Nothing to delete.")
                 print(f"No public access block configuration found for '{args.bucket_name}'.")
             else:
                 logging.error(f"Failed to delete Public Access Block: {e}", exc_info=True)
                 print(f"Error deleting Public Access Block for '{args.bucket_name}'. See logs.")
        except ValueError as e:
             logging.error(f"Failed to delete PAB due to config error: {e}", exc_info=True)
             print(f"Configuration error deleting PAB for '{args.bucket_name}'. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error deleting Public Access Block: {e}")
            print("An unexpected error occurred. See logs.")