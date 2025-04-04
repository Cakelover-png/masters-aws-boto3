from tasks2.task4.main import S3ManagementTask
from tasks3.task1.handler import SetLifecyclePolicyHandler, UploadLargeFileHandler, UploadSmallFileHandler


class ImprovedS3ManagementTask(S3ManagementTask):
    @property
    def name(self) -> str:
        return "task3.1"

    @property
    def usage(self) -> str:
        return super().usage

    def setup_arguments(self):
        subparsers = super().setup_arguments()

        p_upload_small = subparsers.add_parser('upload-small', help='Upload a small file (<5MB recommended) to S3.')
        p_upload_small.add_argument('--bucket-name', required=True, help='Target bucket name.')
        p_upload_small.add_argument('--file-path', required=True, help='Local path of the file to upload.')
        p_upload_small.add_argument('--s3-key', required=True, help='Destination key (path/filename) in S3.')
        p_upload_small.set_defaults(handler_class=UploadSmallFileHandler)

        p_upload_large = subparsers.add_parser('upload-large', help='Upload a large file to S3 using multipart upload.')
        p_upload_large.add_argument('--bucket-name', required=True, help='Target bucket name.')
        p_upload_large.add_argument('--file-path', required=True, help='Local path of the large file to upload.')
        p_upload_large.add_argument('--s3-key', required=True, help='Destination key (path/filename) in S3.')
        p_upload_large.add_argument('--use-standard', action='store_true', help='Use boto3\'s standard upload_file (auto-multipart) instead of manual multipart.')
        p_upload_large.set_defaults(handler_class=UploadLargeFileHandler)

        p_set_lifecycle = subparsers.add_parser('set-lifecycle', help='Set a lifecycle policy to delete objects after N days.')
        p_set_lifecycle.add_argument('--bucket-name', required=True, help='Target bucket name.')
        p_set_lifecycle.add_argument('--days', type=int, default=120, help='Number of days after creation to expire objects. Default: 120.')
        p_set_lifecycle.set_defaults(handler_class=SetLifecyclePolicyHandler)
        
        return subparsers
