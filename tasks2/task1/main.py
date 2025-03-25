import logging
import sys
from core.utils.tasks import BaseTask
from tasks2.utils.client import init_s3_client
from tasks2.utils.s3 import bucket_exists, create_bucket
from botocore.exceptions import ClientError


class S3BucketTask(BaseTask):
    @property
    def name(self) -> str:
        return "task2.1"

    @property
    def small_desc(self) -> str:
        return "Checks existence of an S3 bucket and creates it if missing."

    @property
    def usage(self) -> str:
        return f"python {sys.argv[0]} {self.name} --bucket-name <your-bucket-name>"

    def setup_arguments(self):
        self.parser.add_argument(
            "--bucket-name",
            required=True,
            help="The name of the S3 bucket to check or create.",
            metavar="<bucket-name>"
        )

    def run(self, args):
        bucket_name = args.bucket_name
        logging.info(f"Task '{self.name}': Processing bucket '{bucket_name}'")
        try:
            s3_client = init_s3_client()

            if bucket_exists(s3_client, bucket_name):
                print(f"Bucket '{bucket_name}' already exists.")
            else:
                print(f"Bucket '{bucket_name}' not found or inaccessible. Attempting to create...")
                create_bucket(s3_client, bucket_name)
                print(f"Bucket '{bucket_name}' created successfully.")

        except (ClientError, ValueError) as e:
            logging.error(f"Task '{self.name}' failed for bucket '{bucket_name}': {e}", exc_info=True)
            print(f"Error processing bucket '{bucket_name}'. Operation failed. See logs for details.")
        except Exception as e:
            logging.exception(f"An unexpected error occurred in task '{self.name}' for bucket '{bucket_name}': {e}")
            print(f"An unexpected error occurred while processing bucket '{bucket_name}'. See logs.")

        logging.info(f"Task '{self.name}' finished for bucket '{bucket_name}'.")
