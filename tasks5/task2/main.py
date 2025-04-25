import sys
from core.utils.tasks import BaseTask

from tasks5.task2.handler import InspireHandler

class QuoteTask(BaseTask):
    """Task to fetch inspirational quotes and optionally save them to S3."""

    @property
    def name(self) -> str:
        return "task5.2"

    @property
    def small_desc(self) -> str:
        return "Fetches inspirational quotes and can save them to an S3 bucket."

    @property
    def usage(self) -> str:
        return f"""
        Get a random inspirational quote:
        python {sys.argv[0]} {self.name} inspire
        
        Get quotes by a specific author:
        python {sys.argv[0]} {self.name} inspire --author "Author Name"
        
        Save quotes to S3:
        python {sys.argv[0]} {self.name} inspire --author "Author Name" --bucket-name <bucket_name> --save
        """

    def setup_arguments(self):
        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='Action to perform'
        )
        
        inspire_parser = subparsers.add_parser('inspire', help="Get an inspirational quote")

        inspire_parser.add_argument(
            "--author",
            type=str,
            help="Filter quotes by author name"
        )

        inspire_parser.add_argument(
            "--bucket-name",
            type=str,
            help="S3 bucket name for saving quotes (required with --save)"
        )

        inspire_parser.add_argument(
            "--save",
            action="store_true",
            help="Save the quote to an S3 bucket (requires --bucket-name)"
        )

        inspire_parser.set_defaults(handler_class=InspireHandler)
