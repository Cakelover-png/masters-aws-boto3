import logging
import sys
from botocore.exceptions import ClientError
from core.utils.client import init_s3_client
from core.utils.tasks import BaseTask
from tasks2.utils.s3 import bucket_exists, delete_bucket


class S3DeleteBucketTask(BaseTask):
    @property
    def name(self) -> str:
        return "task2.3"

    @property
    def small_desc(self) -> str:
        return "Checks if an S3 bucket exists and deletes it if found."

    @property
    def usage(self) -> str:
        return f"python {sys.argv[0]} {self.name} --bucket-name <your-bucket-name>"

    def setup_arguments(self):
        self.parser.add_argument(
            "--bucket-name",
            required=True,
            help="The name of the S3 bucket to check and potentially delete.",
            metavar="<bucket-name>"
        )

    def run(self, args):
        bucket_name = args.bucket_name
        logging.info(f"Task '{self.name}': Processing bucket '{bucket_name}' for deletion")

        try:
            s3_client = init_s3_client()

            if bucket_exists(s3_client, bucket_name):
                print(f"Bucket '{bucket_name}' found. Attempting deletion...")

                delete_bucket(s3_client, bucket_name)

                print(f"Bucket '{bucket_name}' deleted successfully.")
            else:
                print(f"Bucket '{bucket_name}' does not exist or is inaccessible.")

        except ClientError as e:
            logging.error(f"Task '{self.name}' failed for bucket '{bucket_name}': {e}", exc_info=True)
            print(f"Error processing bucket '{bucket_name}'. Operation failed.")
            if e.response.get("Error", {}).get("Code") == 'BucketNotEmpty':
                print("Hint: Buckets must be empty before deletion.")
            else:
                print("See logs for details.")
        except ValueError as e:
            logging.error(f"Task '{self.name}' failed due to config error: {e}", exc_info=True)
            print(f"Configuration error processing bucket '{bucket_name}'. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error in task '{self.name}' for bucket '{bucket_name}': {e}")
            print(f"An unexpected error occurred processing '{bucket_name}'. See logs.")

        logging.info(f"Task '{self.name}' finished for bucket '{bucket_name}'.")