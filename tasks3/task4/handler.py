
import argparse
import logging
from core.utils.s3.handlers import BaseS3CommandHandler
from tasks3.utils.s3 import organize_objects_by_extension


class OrganizeByExtensionHandler(BaseS3CommandHandler):
    """Handles the 'organize-by-extension' command."""
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: organize-by-extension for bucket {args.bucket_name}")

        counts = organize_objects_by_extension(
            s3_client=self.client,
            bucket_name=args.bucket_name
        )

        if counts is not None:
            if counts:
                print("\n--- Files Moved per Extension ---")
                for ext, count in sorted(counts.items()):
                    print(f"{ext} - {count}")
                print("---------------------------------")
            else:
                 print("\nNo files were moved (either none at root or none had extensions).")
        else:
            print(f"\nFailed to complete organization for bucket '{args.bucket_name}'. Check logs.")
