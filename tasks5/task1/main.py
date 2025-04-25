import sys
from core.utils.tasks import BaseTask
from tasks5.task1.handler import HostStaticWebsiteHandler

class HostStaticWebsiteTask(BaseTask):
    """Task to host a static website on S3 from a local directory."""

    @property
    def name(self) -> str:
        return "task5.1"

    @property
    def small_desc(self) -> str:
        return "Creates an S3 bucket configured for static website hosting and uploads files from a local directory."

    @property
    def usage(self) -> str:
        return f"python {sys.argv[0]} {self.name} host --bucket-name <s3_bucket_name> --source <local_directory_path>"

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='Action to perform on S3'
        )

        host_website_parser = subparsers.add_parser('host', help=self.small_desc)
        host_website_parser.add_argument(
            "--source",
            type=str,
            required=True,
            help="Path to the local directory containing website files."
        )
        host_website_parser.add_argument(
            "--bucket-name",
            type=str,
            required=True,
            help="Name for the S3 bucket to create for static website hosting."
        )

        host_website_parser.set_defaults(handler_class=HostStaticWebsiteHandler)
