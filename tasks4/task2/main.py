import logging
import sys
from typing import Type
from core.utils.s3.client import init_s3_client
from core.utils.s3.handlers import BaseS3CommandHandler
from core.utils.tasks import BaseTask
from botocore.exceptions import ClientError

from tasks4.task2.handler import DeleteOldVersionsHandler


class DeleteOldVersionsTask(BaseTask):
    """Task to delete old object versions from S3."""

    @property
    def name(self) -> str:
        return "task4.2"

    @property
    def small_desc(self) -> str:
        return "Deletes object versions older than 6 months for specified keys."

    @property
    def usage(self) -> str:
        return f"python {sys.argv[0]} {self.name} --bucket-name <s3_bucket_name> --object-keys <key1> [<key2> ...]"

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='Action to perform on S3'
        )

        delete_old_version_parser = subparsers.add_parser('delete-old-version', help=self.small_desc)
        delete_old_version_parser.add_argument(
            "--bucket-name",
            type=str,
            required=True,
            metavar='<s3_bucket_name>',
            help="Name of the S3 bucket containing the objects."
        )
        delete_old_version_parser.add_argument(
            "--object-keys",
            type=str,
            required=True,
            nargs='+',
            metavar='<s3_object_key>',
            help="One or more S3 object keys (paths) whose old versions should be deleted."
        )
        delete_old_version_parser.set_defaults(handler_class=DeleteOldVersionsHandler)


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