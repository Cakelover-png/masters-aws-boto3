import abc
import argparse

import boto3

class BaseS3CommandHandler(abc.ABC):
    def __init__(self, s3_client: boto3.client):
        self.client = s3_client

    @abc.abstractmethod
    def execute(self, args: argparse.Namespace):
        pass
