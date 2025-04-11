import logging
import sys
from typing import Type
from core.utils.s3.client import init_s3_client
from core.utils.s3.handlers import BaseS3CommandHandler
from core.utils.tasks import BaseTask
from botocore.exceptions import ClientError

from tasks4.task3.handler import HostStaticHandler



class HostStaticSiteTask(BaseTask):
    """Task to set up S3 static website hosting with a basic index.html."""

    @property
    def name(self) -> str:
        return "task4.3"

    @property
    def small_desc(self) -> str:
        return "Creates index.html, uploads, enables S3 hosting & public policy."

    @property
    def usage(self) -> str:
        return (f"python {sys.argv[0]} {self.name} --bucket-name <s3_bucket_name> "
                f"--first-name <first_name> --last-name <last_name>")

    def setup_arguments(self):
        """Adds arguments specific to the host-static-site task."""
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='Action to perform on S3'
        )

        host_static_site_parser = subparsers.add_parser('host-static-site', help=self.small_desc)
        host_static_site_parser.add_argument(
            "--bucket-name",
            type=str,
            required=True,
            metavar='<s3_bucket_name>',
            help="Name of the S3 bucket to configure for hosting (must be globally unique)."
        )
        host_static_site_parser.add_argument(
            "--first-name",
            type=str,
            required=True,
            metavar='<first_name>',
            help="First name to display on the index page."
        )
        host_static_site_parser.add_argument(
            "--last-name",
            type=str,
            required=True,
            metavar='<last_name>',
            help="Last name to display on the index page."
        )
        host_static_site_parser.set_defaults(handler_class=HostStaticHandler)

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