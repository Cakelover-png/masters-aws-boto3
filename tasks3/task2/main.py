from tasks3.task1.main import ImprovedS3ManagementTask
from tasks3.task2.handler import DeleteObjectHandler


class ObjectRemovalS3ManagementTask(ImprovedS3ManagementTask):
    @property
    def name(self) -> str:
        return "task3.2"

    @property
    def usage(self) -> str:
        return super().usage

    def setup_arguments(self):
        subparsers = super().setup_arguments()
        p_delete_object = subparsers.add_parser('delete-object', help='Delete a specific object from an S3 bucket.')
        p_delete_object.add_argument('--bucket-name', required=True, help='Name of the bucket containing the object.')
        p_delete_object.add_argument('--key', required=True, help='Key (path/filename) of the object to delete.')
        p_delete_object.set_defaults(handler_class=DeleteObjectHandler)
        
        return subparsers
