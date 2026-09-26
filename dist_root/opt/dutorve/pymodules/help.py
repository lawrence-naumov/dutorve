import sys

from .base import Subparser


class HelpParser(Subparser):
    command = "help"
    help = "Show help message for any command"

    def add_args(self) -> None:
        self.subparser.add_argument(
            "help_command",
            help="Show help for specific command",
            metavar="command",
            nargs="?",
        )

    def run(self, args) -> None:
        if getattr(args, "help_command", None):
            try:
                self.subparsers.choices[args.help_command].print_help()
            except KeyError, AttributeError:
                print(
                    f"Invalid command '{args.help_command}'"
                    f"use one of {
                        ', '.join(
                            "'" + command + "'"
                            for command in self.subparsers.choices.keys()
                        )
                    }\n\n",
                    file=sys.stderr,
                )
            else:
                exit(0)
        self.parser.print_help()
