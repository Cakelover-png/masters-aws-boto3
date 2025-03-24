from abc import ABC, abstractmethod
import argparse

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

    @abstractmethod
    def run(self, args):
        """Main execution logic that must be implemented by subclasses"""
        pass

    def execute(self):
        args = self.parser.parse_args()
        if args.desc:
            print(f"Task: {self.name}")
            print(f"Description: {self.small_desc}")
            print(f"Usage: {self.usage}")
            return
        self.run(args)