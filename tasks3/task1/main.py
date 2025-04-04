from tasks2.task4.main import S3ManagementTask


class ImprovedS3ManagementTask(S3ManagementTask):
    @property
    def name(self) -> str:
        return "task3.1"
    
