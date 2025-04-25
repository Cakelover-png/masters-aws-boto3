import argparse
from core.utils.s3.handlers import BaseS3CommandHandler
from tasks5.utils.s3 import host_static_website

class HostStaticWebsiteHandler(BaseS3CommandHandler):
    """Handles hosting a static website on S3 from a local directory."""

    def execute(self, args: argparse.Namespace):
        """
        Executes the static website hosting process using the provided arguments.
        """
        success, website_url = host_static_website(
            s3_client=self.client,
            bucket_name=args.bucket_name,
            source_folder=args.source
        )

        if success:
            print(f"Successfully deployed static website from '{args.source}'")
            print(f"Your website is now available at: {website_url}")
        else:
            print(f"Failed to deploy static website from '{args.source}' to bucket '{args.bucket_name}'.")
