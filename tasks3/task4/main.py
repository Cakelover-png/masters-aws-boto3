from tasks3.task2.main import ObjectRemovalS3ManagementTask
from tasks3.task4.handler import OrganizeByExtensionHandler


class OrginizeS3ManagementTask(ObjectRemovalS3ManagementTask):
    @property
    def name(self) -> str:
        return "task3.4"

    @property
    def usage(self) -> str:
        return super().usage

    def setup_arguments(self):
        subparsers = super().setup_arguments()
        p_organize = subparsers.add_parser(
            'organize-by-extension',
            help='Move root objects into folders named after their file extensions.',
            description='Scans the root of the bucket, identifies file extensions,'
            ' creates corresponding folders (prefixes), and moves the files into them. Reports counts per extension.'
        )
        p_organize.add_argument('--bucket-name', required=True, help='Name of the bucket to organize.')
        p_organize.set_defaults(handler_class=OrganizeByExtensionHandler)
        return subparsers
