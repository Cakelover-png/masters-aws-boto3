import sys
import logging
from typing import Type
from botocore.exceptions import ClientError
from core.utils.tasks import BaseTask
from tasks2.task4.handler import BaseS3CommandHandler, BucketExistsHandler, CreateBucketHandler, DeleteBucketHandler, DeletePublicAccessBlockHandler, GetBucketPolicyHandler, ListBucketsHandler, SetBucketPolicyHandler, SetObjectAclHandler, UploadObjectHandler
from tasks2.utils.client import init_s3_client


class S3ManagementTask(BaseTask):
    @property
    def name(self) -> str:
        return "task2.4"

    @property
    def small_desc(self) -> str:
        return "Manage S3 buckets and objects (list, create, delete, upload, policies)."

    @property
    def usage(self) -> str:
        # Build a more informative usage string dynamically
        base_usage = f"python {sys.argv[0]} {self.name} <command> [options...]"
        commands = self.get_capabilities()
        if commands:
             cmd_list = ", ".join(commands.keys())
             return f"{base_usage}\nAvailable commands: {cmd_list}"
        return base_usage


    def setup_arguments(self):

        subparsers = self.parser.add_subparsers(
            dest='command',
            required=True,
            title='Available commands',
            metavar='<command>',
            help='Action to perform on S3'
        )
        # --- Subcommand definitions ---
        p_list = subparsers.add_parser('list', help='List accessible S3 buckets.')
        p_list.set_defaults(handler_class=ListBucketsHandler)

        p_exists = subparsers.add_parser('exists', help='Check if a bucket exists.')
        p_exists.add_argument('--bucket-name', required=True, help='Name of the bucket.')
        p_exists.set_defaults(handler_class=BucketExistsHandler)

        p_create = subparsers.add_parser('create', help='Create a new S3 bucket.')
        p_create.add_argument('--bucket-name', required=True, help='Name for the new bucket.')
        p_create.set_defaults(handler_class=CreateBucketHandler)

        p_delete = subparsers.add_parser('delete', help='Delete an existing S3 bucket (must be empty!).')
        p_delete.add_argument('--bucket-name', required=True, help='Name of the bucket to delete.')
        p_delete.set_defaults(handler_class=DeleteBucketHandler)

        p_upload = subparsers.add_parser('upload', help='Download from URL and upload to S3.')
        p_upload.add_argument('--bucket-name', required=True, help='Target bucket name.')
        p_upload.add_argument('--url', required=True, help='URL of the file to download.')
        p_upload.add_argument('--s3-key', required=True, help='Destination key (path/filename) in S3.')
        p_upload.set_defaults(handler_class=UploadObjectHandler)

        p_set_acl = subparsers.add_parser('set-object-acl', help='Set ACL for an S3 object.')
        p_set_acl.add_argument('--bucket-name', required=True, help='Bucket name.')
        p_set_acl.add_argument('--s3-key', required=True, help='Object key.')
        p_set_acl.add_argument('--acl', required=True, choices=[
            'private', 'public-read', 'public-read-write', 'authenticated-read',
            'aws-exec-read', 'bucket-owner-read', 'bucket-owner-full-control'],
            help='Canned ACL to apply.')
        p_set_acl.set_defaults(handler_class=SetObjectAclHandler)

        p_get_policy = subparsers.add_parser('get-policy', help='Read the policy of an S3 bucket.')
        p_get_policy.add_argument('--bucket-name', required=True, help='Bucket name.')
        p_get_policy.set_defaults(handler_class=GetBucketPolicyHandler)

        p_set_policy = subparsers.add_parser('set-policy',
            help="Apply a public-read policy to a bucket. WARNING: Overwrites existing policy!",
            description="Applies a standard public-read policy. Attempts to delete Public Access Block unless --skip-pab-delete is used. Exits if policy exists.")
        p_set_policy.add_argument('--bucket-name', required=True, help='Bucket name.')
        p_set_policy.add_argument('--skip-pab-delete', action='store_true', help="Don't attempt to delete Public Access Block first.")
        p_set_policy.set_defaults(handler_class=SetBucketPolicyHandler)

        p_delete_pab = subparsers.add_parser('delete-pab', help='Delete the Public Access Block configuration for a bucket.')
        p_delete_pab.add_argument('--bucket-name', required=True, help='Bucket name.')
        p_delete_pab.set_defaults(handler_class=DeletePublicAccessBlockHandler)

    def run(self, args):
        s3_client = None
        try:
            s3_client = init_s3_client()

            if not hasattr(args, 'handler_class'):
                 # This should ideally be caught by argparse 'required=True'
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