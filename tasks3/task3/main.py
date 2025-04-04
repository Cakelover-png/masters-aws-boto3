from tasks3.task2.main import ObjectRemovalS3ManagementTask
from tasks3.task3.handler import GetVersioningHandler, ListVersionsHandler, RestorePreviousVersionHandler


class VersioningS3ManagementTask(ObjectRemovalS3ManagementTask):
    @property
    def name(self) -> str:
        return "task3.3"

    @property
    def usage(self) -> str:
        return super().usage

    def setup_arguments(self):
        subparsers = super().setup_arguments()
        p_get_versioning = subparsers.add_parser('get-versioning', help='Check if versioning is enabled for a bucket.')
        p_get_versioning.add_argument('--bucket-name', required=True, help='Name of the bucket to check.')
        p_get_versioning.set_defaults(handler_class=GetVersioningHandler)

        p_list_versions = subparsers.add_parser('list-versions', help='List versions of a specific object.')
        p_list_versions.add_argument('--bucket-name', required=True, help='Name of the bucket containing the object.')
        p_list_versions.add_argument('--key', required=True, help='Key (path/filename) of the object.')
        p_list_versions.set_defaults(handler_class=ListVersionsHandler)

        p_restore_previous = subparsers.add_parser('restore-previous', help='Restore the previous version of an object to be the latest.')
        p_restore_previous.add_argument('--bucket-name', required=True, help='Name of the bucket containing the object.')
        p_restore_previous.add_argument('--key', required=True, help='Key (path/filename) of the object.')
        p_restore_previous.set_defaults(handler_class=RestorePreviousVersionHandler)
        return subparsers
