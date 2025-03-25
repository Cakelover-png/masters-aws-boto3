import logging
import json
import sys
from botocore.exceptions import ClientError
from core.utils.tasks import BaseTask
from tasks2.utils.client import init_s3_client
from tasks2.utils.s3 import apply_bucket_policy, delete_public_access_block, read_bucket_policy



def generate_dev_test_public_policy(bucket_name: str) -> str:
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadDevTestPrefixes",
            "Effect": "Allow",
            "Principal": "*", 
            "Action": ["s3:GetObject"],
            "Resource": [
                f"arn:aws:s3:::{bucket_name}/dev/*",
                f"arn:aws:s3:::{bucket_name}/test/*"
            ]
        }]
    }
    return json.dumps(policy)



class S3PublicPolicyTask(BaseTask):
    @property
    def name(self) -> str:
        return "task2.2"

    @property
    def small_desc(self) -> str:
        return "Checks/Applies a public-read policy for dev/ and test/ prefixes."

    @property
    def usage(self) -> str:
        return f"python {sys.argv[0]} {self.name} --bucket-name <your-bucket-name>"

    def setup_arguments(self):
        self.parser.add_argument(
            "--bucket-name",
            required=True,
            help="The name of the S3 bucket to check/update policy for.",
            metavar="<bucket-name>"
        )

    def run(self, args):
        bucket_name = args.bucket_name
        logging.info(f"Task '{self.name}': Processing policy for bucket '{bucket_name}'")

        try:
            s3_client = init_s3_client()

            if read_bucket_policy(s3_client, bucket_name):
                print(f"Bucket '{bucket_name}' already has a policy.")
            else:
                print(f"No policy found for '{bucket_name}'. Applying policy...")

                delete_public_access_block(s3_client, bucket_name)

                new_policy = generate_dev_test_public_policy(bucket_name)
                apply_bucket_policy(s3_client, bucket_name, new_policy)

                print(f"Successfully applied policy to bucket '{bucket_name}'.")

        except (ClientError, ValueError) as e:
            logging.error(f"Task '{self.name}' failed for bucket '{bucket_name}': {e}", exc_info=True)
            print(f"Error processing policy for bucket '{bucket_name}'. Operation failed. See logs.")
        except Exception as e:
            logging.exception(f"Unexpected error in task '{self.name}' for bucket '{bucket_name}': {e}")
            print(f"An unexpected error occurred processing '{bucket_name}'. See logs.")

        logging.info(f"Task '{self.name}' finished for bucket '{bucket_name}'.")