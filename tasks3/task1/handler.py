
import argparse
import logging
from core.utils.s3.handlers import BaseS3CommandHandler
from tasks3.utils.s3 import set_delete_lifecycle_policy, upload_large_file, upload_small_file


class UploadSmallFileHandler(BaseS3CommandHandler):
    """Handles the 'upload-small' command."""
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: upload-small for file {args.file_path}")
        try:
            success = upload_small_file(
                s3_client=self.client,
                bucket_name=args.bucket_name,
                file_path=args.file_path,
                object_key=args.s3_key
            )
            if success:
                print(f"Successfully uploaded small file '{args.file_path}' to 's3://{args.bucket_name}/{args.s3_key}'.")
            else:
                print(f"Failed to upload small file '{args.file_path}'. Check logs.")
        except Exception as e:
            logging.exception(f"Unexpected error during small file upload command: {e}")
            print(f"An unexpected error occurred uploading '{args.file_path}'. See logs.")


class UploadLargeFileHandler(BaseS3CommandHandler):
    """Handles the 'upload-large' command."""
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: upload-large for file {args.file_path}")

        try:
            success = upload_large_file(
                s3_client=self.client,
                bucket_name=args.bucket_name,
                file_path=args.file_path,
                object_key=args.s3_key,
                use_standard_method=args.use_standard,
            )
            if success:
                method = "standard (automatic multipart)" if args.use_standard else "manual multipart"
                print(f"Successfully uploaded large file '{args.file_path}' to 's3://{args.bucket_name}/{args.s3_key}' using {method} method.")
            else:
                print(f"Failed to upload large file '{args.file_path}'. Check logs.")
        except Exception as e:
            logging.exception(f"Unexpected error during large file upload command: {e}")
            print(f"An unexpected error occurred uploading '{args.file_path}'. See logs.")


class SetLifecyclePolicyHandler(BaseS3CommandHandler):
    """Handles the 'set-lifecycle' command."""
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: set-lifecycle for bucket {args.bucket_name} with expiration {args.days} days")
        try:
            success = set_delete_lifecycle_policy(
                s3_client=self.client,
                bucket_name=args.bucket_name,
                days_to_expiration=args.days
            )
            if success:
                print(f"Successfully set/updated lifecycle policy on bucket '{args.bucket_name}'.")
            else:
                print(f"Failed to set lifecycle policy on bucket '{args.bucket_name}'. Check logs.")
        except Exception as e:
            logging.exception(f"Unexpected error during set lifecycle policy command: {e}")
            print(f"An unexpected error occurred setting lifecycle policy for '{args.bucket_name}'. See logs.")
