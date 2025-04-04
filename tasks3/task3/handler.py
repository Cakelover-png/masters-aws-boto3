
import argparse
import logging
from core.utils.s3.handlers import BaseS3CommandHandler
from tasks3.utils.s3 import get_bucket_versioning_status, list_object_versions, restore_previous_version


class GetVersioningHandler(BaseS3CommandHandler):
    """Handles the 'get-versioning' command."""
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: get-versioning for bucket {args.bucket_name}")
        get_bucket_versioning_status(self.client, args.bucket_name)

class ListVersionsHandler(BaseS3CommandHandler):
    """Handles the 'list-versions' command."""
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: list-versions for s3://{args.bucket_name}/{args.key}")
        versions = list_object_versions(self.client, args.bucket_name, args.key)

        if versions is not None and versions:
             print("\n--- Object Versions ---")
             print(f"{'Version ID':<70} {'Last Modified':<28} {'Size (Bytes)':<15} {'Is Latest':<10} {'Type':<15}")
             print("-" * 140)
             for v in versions:
                 version_id = v.get('VersionId', 'N/A')
                 last_modified = v['LastModified'].strftime('%Y-%m-%d %H:%M:%S %Z')
                 size = str(v.get('Size', 'N/A'))
                 is_latest = str(v.get('IsLatest', 'N/A'))
                 type_str = v.get('Type', 'Version') # Default to 'Version' if Type key missing
                 print(f"{version_id:<70} {last_modified:<28} {size:<15} {is_latest:<10} {type_str:<15}")
             print("-" * 140)
             print(f"Total items listed: {len(versions)}")
        elif versions is not None:
             pass
        else:
             print(f"Failed to list versions for 's3://{args.bucket_name}/{args.key}'. Check logs.")

class RestorePreviousVersionHandler(BaseS3CommandHandler):
    """Handles the 'restore-previous' command."""
    def execute(self, args: argparse.Namespace):
        logging.info(f"Executing command: restore-previous for s3://{args.bucket_name}/{args.key}")
        success = restore_previous_version(
            s3_client=self.client,
            bucket_name=args.bucket_name,
            object_key=args.key
        )
        if not success:
             print(f"Failed to restore previous version for 's3://{args.bucket_name}/{args.key}'. Check logs.")