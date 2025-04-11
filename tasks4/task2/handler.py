
import argparse
from core.utils.s3.handlers import BaseS3CommandHandler
from tasks4.utils.s3 import simple_delete_old_versions


class DeleteOldVersionsHandler(BaseS3CommandHandler):
    """Handles deleting old object versions (simplified execution)."""

    def execute(self, args: argparse.Namespace):

        deleted_count = simple_delete_old_versions(
            s3_client=self.client,
            bucket_name=args.bucket_name,
            object_keys=args.object_keys
        )

        print("\n--- Deletion Summary ---")
        if deleted_count == -1:
            print("A critical error occurred during the delete operation. Check logs.")
        elif deleted_count == 0:
            print("No old versions were found matching the criteria or specified keys.")
        elif deleted_count > 0:
            print(f"Attempted to delete {deleted_count} old version(s). Check logs for any specific errors reported by AWS.")
        else:
             print("Unexpected return value from deletion function.")