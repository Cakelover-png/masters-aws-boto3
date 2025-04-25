from abc import ABC, abstractmethod
import argparse
import logging
from typing import Type

from core.utils.s3.client import init_s3_client
from core.utils.s3.handlers import BaseS3CommandHandler
from botocore.exceptions import ClientError


class BaseTask(ABC):
    def __init__(self):
        self.parser = argparse.ArgumentParser(description=f"Task: {self.name}")
        self.parser.add_argument("--desc", action="store_true", help="Display task description")
        self.setup_arguments()

    @property
    @abstractmethod
    def name(self) -> str:
        """Task name that must be implemented by subclasses"""
        pass

    @property
    @abstractmethod
    def small_desc(self) -> str:
        """Short description that must be implemented by subclasses"""
        pass

    @property
    def usage(self) -> str:
        """Task usage that must be implemented by subclasses"""
        pass

    @abstractmethod
    def setup_arguments(self):
        """Method to add additional arguments specific to the task"""
        pass

    def execute(self):
        args = self.parser.parse_args()
        if args.desc:
            print(f"Task: {self.name}")
            print(f"Description: {self.small_desc}")
            print(f"Usage: {self.usage}")
            return
        self.run(args)

    def run(self, args):
        s3_client = None
        try:
            s3_client = init_s3_client()

            if not hasattr(args, 'handler_class'):
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