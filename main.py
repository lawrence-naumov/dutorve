#!/usr/bin/env python3
import argparse
from pymodules.help import HelpParser
from pymodules.run import RunParser
from pymodules.inventory import InventoryParser


def main():
    parser = argparse.ArgumentParser(
        description="Configure hosts with prepared ansible playbooks",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=False, help="command")

    help_parser = HelpParser(parser, subparsers)
    RunParser(parser, subparsers)
    InventoryParser(parser, subparsers)
    args = parser.parse_args()
    if not args.command:
        help_parser.run(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
