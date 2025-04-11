import logging
import sys
from typing import Type
from core.utils.s3.client import init_s3_client
from core.utils.s3.handlers import BaseS3CommandHandler
from core.utils.tasks import BaseTask
from botocore.exceptions import ClientError

from tasks4.task1.handler import UploadByTypeHandler



class UploadByTypeTask(BaseTask):
    """Task to upload a local file to S3, organizing by MIME type."""

    @property
    def name(self) -> str:
        return "task4.1"

    @property
    def small_desc(self) -> str:
        return "Uploads a local file to an S3 bucket, placing it in a folder named after its detected MIME type (using python-magic)."

    @property
    def usage(self) -> str:
        return f"python {sys.argv[0]} {self.name} --file <local_file_path> --bucket <s3_bucket_name>"

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='Action to perform on S3'
        )

        upload_by_type_parser = subparsers.add_parser('upload-by-type', help=self.small_desc)
        upload_by_type_parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to the local file to upload."
        )
        upload_by_type_parser.add_argument(
            "--bucket-name",
            type=str,
            required=True,
            help="Name of the target S3 bucket."
        )

        upload_by_type_parser.set_defaults(handler_class=UploadByTypeHandler)



    def run(self, args):
        s3_client = None
        try:
            s3_client = init_s3_client()

            if not hasattr(args, 'handler_class'):
                 logging.error(f"No handler class defined for command: {args.command}")
                 print(f"Error: Command '{args.command}' is not properly configured.")
                 self.parser.print_help()
                 return

            handler_class: Type[BaseS3CommandHandler] = args.handler_class
            handler_instance = handler_class(s3_client)
            handler_instance.execute(args)

        except (ClientError, ValueError) as e:
            logging.error(f"A configuration or AWS client error occurred: {e}", exc_info=True)
            print(f"Error during setup or execution: {e}. See logs.")
        except AttributeError as ae:
             if 'handler_class' in str(ae):
                  logging.error(f"Developer error: No handler_class set for command '{args.command}'.", exc_info=True)
                  print(f"Internal error: Command '{args.command}' is not configured correctly.")
             else:
                  logging.exception(f"An unexpected attribute error occurred: {ae}")
                  print("An unexpected internal error occurred. See logs.")
        except Exception as e:
            logging.exception(f"An unexpected error occurred in the main task runner: {e}")
            print("An unexpected error occurred. See logs for details.")