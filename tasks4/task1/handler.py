
import argparse
from core.utils.s3.handlers import BaseS3CommandHandler
from tasks4.utils.s3 import upload_file_by_type


class UploadByTypeHandler(BaseS3CommandHandler):
    """Handles uploading a file to S3, organized by its detected MIME type."""

    def execute(self, args: argparse.Namespace):
        """
        Executes the file upload process using the provided arguments.
        """
        success, s3_key = upload_file_by_type(
            s3_client=self.client,
            bucket_name=args.bucket_name,
            local_file_path=args.file
        )

        if success:
            print(f"\n Successfully uploaded '{args.file}' to s3://{args.bucket_name}/{s3_key}")
        else:
            print(f"\n Failed to upload '{args.file}' to bucket '{args.bucket_name}'.")