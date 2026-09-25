#!/usr/bin/env python3
from abc import ABC, abstractmethod
import getpass
import argparse
import subprocess
import sys
import os
import traceback
import pathlib
import webbrowser
import yaml


BIN_DIRECTORY = pathlib.Path("/usr/local/bin")
PROJECT_URL = "https://github.com/prostoLavr/ansible-system-setup.git"
SSH_URL = "git@github.com:prostoLavr/ansible-system-setup.git"
PROJECT_DIRECTORY = pathlib.Path.home() / ".test-system-setup"
INVENTORY_FILE = pathlib.Path("inventory.yml")
VAULT_PASS_FILE = pathlib.Path(".vault_pass")
COMMAND_NAME = "test-system-setup"


class VaultString(str):
    @staticmethod
    def representer(dumper, data):
        return dumper.represent_scalar("!vault", data, style="|")

    @classmethod
    def constructor(cls, loader, node):
        return cls(loader.construct_scalar(node))


yaml.SafeDumper.add_representer(VaultString, VaultString.representer)
yaml.SafeLoader.add_constructor("!vault", VaultString.constructor)


class NonInteractiveShellError(Exception):
    def __init__(self, prompt) -> None:
        msg = f"Your shell is not interactive while the program requires answer for `{prompt}`"
        super().__init__(msg)


def ask(prompt, default=None):
    if default is None and not sys.stdin.isatty():
        raise NonInteractiveShellError(prompt)
    default_str = " (y/n) "
    if default is True:
        default_str = " (Y/n) "
    elif default is False:
        default_str = " (y/N) "
    enter_str = "Please enter 'Y' or 'N'."
    if default is not None:
        enter_str = f"Please enter 'Y', 'N' or empty string as default {'Y' if default else 'N'}."

    while True:
        user_input = input(prompt + default_str).strip().lower()
        if default is not None and user_input == "":
            return default
        if user_input in ["y", "yes"]:
            return True
        elif user_input in ["n", "no"]:
            return False
        else:
            print(f"Invalid input. {enter_str}")


def update():
    pass


def run_ansible(game_mode):
    command = [
        "ansible-playbook",
        "-i",
        INVENTORY_FILE,
        "setup-playbook.yml",
        "--ask-vault-pass",
    ]

    game_mode_str = "true" if game_mode else "false"
    command.extend(["-e", f"setup_game_mode={game_mode_str}"])

    print("Start to install...")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print("Ansible Playbook Error", file=sys.stderr)
        sys.exit(1)
    print("Install success!")


def install_project():
    PROJECT_DIRECTORY.parent.mkdir(exist_ok=True, parents=True)
    os.chdir(PROJECT_DIRECTORY.parent)
    # TODO: Make better exceptions for making project parent directory
    exceptions = []
    # TODO: check is git available
    for url in SSH_URL, PROJECT_URL:
        try:
            subprocess.run(["git", "clone", url, PROJECT_DIRECTORY.name], check=True)
        except subprocess.CalledProcessError as exc:
            exceptions.append(exc)
        else:
            if ask("Create system symlink?", default=True):
                create_system_symlink()
            return
    for exc in exceptions:
        traceback.print_exception(exc)
    print("Failed to install project with exceptions above", file=sys.stderr)


def is_root() -> bool:
    return os.geteuid() == 0


def create_system_symlink():
    commands = [
        ["chmod", "755", PROJECT_DIRECTORY / "configure.py"],
        ["ln", "-fs", PROJECT_DIRECTORY / "configure.py", BIN_DIRECTORY / COMMAND_NAME],
        ["chown", "-h", "root:root", BIN_DIRECTORY / COMMAND_NAME],
    ]

    if not is_root():
        commands = [["sudo"] + command for command in commands]

    for command in commands:
        subprocess.run(command, check=True)


def go_to_project():
    try:
        os.chdir(PROJECT_DIRECTORY)
    except FileNotFoundError:
        if ask("Project directory was not found. Do you want to install?"):
            install_project()
            os.chdir(PROJECT_DIRECTORY)
        else:
            exit(1)


class Subparser(ABC):
    command: str
    help: str
    description: str | None = None

    def __new__(cls, subparsers) -> None:
        subparser = cls._add_self_as_subparser(subparsers)
        cls.add_args(subparser)
        subparser.subparsers = subparsers
        subparser.run = cls.run
        return subparser

    @classmethod
    def add_args(cls, subparser) -> None:
        pass

    @classmethod
    @abstractmethod
    def run(cls, args) -> None:
        pass

    @classmethod
    def _add_self_as_subparser(cls, subparsers):
        return subparsers.add_parser(
            cls.command,
            help=cls.help,
            description=cls.description,
        )


class WorkdirParser(Subparser):
    command = "workdir"
    help = "Show project working directory"

    @classmethod
    def run(cls, args) -> None:
        print(PROJECT_DIRECTORY)


class InventoryParser(Subparser):
    command = "inventory"
    help = "Update ansible inventory file"
    description = "TODO"

    @classmethod
    def add_args(cls, subparser) -> None:
        subparser.add_argument(
            "-l",
            "--local",
            help="Update local password",
            action="store_true",
        )
        subparser.add_argument(
            "-i",
            "--inventory",
            help="Invenotory file",
            type=str,
            default="inventory.yaml",
        )

    @classmethod
    def run(cls, args) -> None:
        default_content = {"all": {"hosts": {}}}
        try:
            with open(args.inventory, mode="r") as inventory:
                content = yaml.safe_load(inventory)
            print(content)
        except FileNotFoundError:
            content = default_content
        if args.local:
            password = cls.get_local_password()
            encrypted_password = cls.enctypt_password(password)
            content["all"]["hosts"]["localhost"] = {
                "ansible_connection": "local",
                "ansible_python_interpreter": "/usr/bin/python3",
                "ansible_sudo_pass": encrypted_password,
            }
        with open(args.inventory, mode="w") as inventory:
            yaml.safe_dump(
                content, inventory, default_flow_style=False, sort_keys=False
            )

    @classmethod
    def enctypt_password(cls, password: str) -> VaultString:
        result = subprocess.run(
            [
                "ansible-vault",
                "encrypt_string",
                "--stdin-name=ansible_sudo_pass",
            ],
            input=password,
            text=True,
            capture_output=True,
        )
        return yaml.safe_load(result.stdout)["ansible_sudo_pass"]

    @classmethod
    def get_local_password(cls):
        while True:
            password = getpass.getpass("Enter the password for your local machine: ")
            result = subprocess.run(
                [
                    "su",
                    "-c",
                    '"true"',
                    getpass.getuser(),
                ],
                input=password,
                text=True,
                capture_output=True,
            )
            if result.returncode == 0:
                return password
            print("Incorrect password. Repeat")


class RunParser(Subparser):
    command = "run"
    help = "Run installation and software configuration"

    @classmethod
    def add_args(cls, subparser) -> None:
        subparser.add_argument(
            "--game",
            "-g",
            action="store_true",
            help="Optimize network drivers for gaming",
        )

    @classmethod
    def run(cls, args) -> None:
        go_to_project()
        run_ansible(game_mode=args.game)


class UpdateParser(Subparser):
    command = "update"
    help = "Update system-setup from github"
    description = None

    @classmethod
    def add_args(cls, subparser) -> None:
        pass

    @classmethod
    def run(cls, args) -> None:
        pass
        # TODO: implementation


class OpenRepoParser(Subparser):
    command = "open-repo"
    help = "Open repo page"
    description = None

    @classmethod
    def run(cls, args) -> None:
        webbrowser.open(PROJECT_URL)


def main():
    parser = argparse.ArgumentParser(
        description="Lawrence's system setup CLI tool",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=False, help="command")
    help_parser = subparsers.add_parser(
        "help",
        help="Show help message for any command",
    )
    help_parser.add_argument(
        "help_command",
        help="Show help for specific command",
        metavar="command",
        nargs="?",
    )

    RunParser(subparsers)
    InventoryParser(subparsers)
    OpenRepoParser(subparsers)
    WorkdirParser(subparsers)
    UpdateParser(subparsers)
    args = parser.parse_args()

    if args.command == "help" or not args.command:
        if getattr(args, "help_command", None):
            try:
                subparsers.choices[args.help_command].print_help()
            except KeyError, AttributeError:
                print(
                    f"Invalid command '{args.help_command}'"
                    f"use one of {
                        ', '.join(
                            "'" + command + "'" for command in subparsers.choices.keys()
                        )
                    }\n\n",
                    file=sys.stderr,
                )
            else:
                exit(0)
        parser.print_help()
        exit(0)

    subparsers.choices[args.command].run(args)  # TODO: fix typing


if __name__ == "__main__":
    main()
