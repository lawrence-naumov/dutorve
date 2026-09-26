#!/usr/bin/env python3
import argparse
import pathlib


BIN_DIRECTORY = pathlib.Path("/usr/local/bin")
PROJECT_URL = "https://github.com/prostoLavr/ansible-system-setup.git"
SSH_URL = "git@github.com:prostoLavr/ansible-system-setup.git"
PROJECT_DIRECTORY = pathlib.Path.home() / ".test-system-setup"
INVENTORY_FILE = pathlib.Path("inventory.yml")
VAULT_PASS_FILE = pathlib.Path(".vault_pass")
COMMAND_NAME = "test-system-setup"


def main():
    parser = argparse.ArgumentParser(
        description="Lawrence's system setup CLI tool",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=False, help="command")

    help_parser = HelpParser(parser, subparsers)
    RunParser(parser, subparsers)
    InventoryParser(parser, subparsers)
    OpenRepoParser(parser, subparsers)
    WorkdirParser(parser, subparsers)
    UpdateParser(parser, subparsers)
    args = parser.parse_args()
    if not args.command:
        help_parser.run(args)
    else:
        args.func(args)  # TODO: fix typing


if __name__ == "__main__":
    main()
