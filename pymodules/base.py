from abc import ABC, abstractmethod
import argparse


class Subparser(ABC):
    command: str
    help: str
    description: str | None = None

    def __init__(self, parser: argparse.ArgumentParser, subparsers) -> None:
        self.parser = parser
        self.subparsers = subparsers
        self.subparser = subparsers.add_parser(
            self.command,
            help=self.help,
            description=self.description,
        )
        self.add_args()
        self.subparser.set_defaults(func=self.run)

    def add_args(self) -> None:
        pass

    @abstractmethod
    def run(self, args) -> None:
        pass
