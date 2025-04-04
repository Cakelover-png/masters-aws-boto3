
import argparse
import logging
from core.utils.s3.handlers import BaseS3CommandHandler
from tasks3.utils.s3 import delete_s3_object


class DeleteObjectHandler(BaseS3CommandHandler):
    """Handles the 'delete-object' command."""
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: delete-object for s3://{args.bucket_name}/{args.key}")
        try:
            success = delete_s3_object(
                s3_client=self.client,
                bucket_name=args.bucket_name,
                object_key=args.key
            )
            if success:
                pass
            else:
                print(f"Failed to delete object 's3://{args.bucket_name}/{args.key}'. Check logs.")
        except Exception as e:
            logging.exception(f"Unexpected error during delete-object command: {e}")
            print(f"An unexpected error occurred deleting 's3://{args.bucket_name}/{args.key}'. See logs.")