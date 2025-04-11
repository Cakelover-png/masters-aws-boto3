
import argparse
from core.utils.s3.handlers import BaseS3CommandHandler
from tasks4.utils.s3 import setup_static_website


class HostStaticHandler(BaseS3CommandHandler):
    """Handles setting up S3 static website hosting."""

    def execute(self, args: argparse.Namespace):
        success, website_url = setup_static_website(
            s3_client=self.client,
            bucket_name=args.bucket_name,
            first_name=args.first_name,
            last_name=args.last_name
        )

        print("\n--- Static Website Hosting Setup ---")
        if success:
            print("Successfully configured static website hosting.")
            print(f"   Bucket: {args.bucket_name}")
            print(f"   Content: index.html with name '{args.first_name} {args.last_name}'")
            print("   Policy: Public Read applied")
            print(f"\n   Website URL: {website_url}")
            print("\n   Note: DNS propagation may take a few moments.")
        else:
            print(f"Failed to set up static website hosting for bucket '{args.bucket_name}'.")
            print("   Check logs for details (e.g., permissions, bucket existence).")
            print("   Required permissions often include: s3:PutObject, s3:PutBucketWebsite, s3:PutBucketPolicy, s3:GetBucketLocation.")