#!/usr/bin/env python3
import argparse
import getpass
import os
import pathlib
import subprocess
import sys
import traceback
import webbrowser
from abc import ABC, abstractmethod
from typing import Any

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


class WorkdirParser(Subparser):
    command = "workdir"
    help = "Show project working directory"

    def run(self, args) -> None:
        print(PROJECT_DIRECTORY)


class InventoryParser(Subparser):
    command = "inventory"
    help = "Ansible inventory file"

    def add_args(self) -> None:
        self.subparser.add_argument(
            "hostname",
            type=str,
            help="Local name of host (leave empty to get list)",
            nargs="?",
        )
        self.subparser.add_argument(
            "-i",
            "--inventory",
            help="Invenotory file",
            type=str,
            default="inventory.yaml",
        )
        self.subparser.add_argument(
            "--rm", help="Remove existing values", action="store_true"
        )
        self.subparser.add_argument(
            "-g",
            "--group",
            action="append",
            type=str,
        )

        connection = self.subparser.add_argument_group("Connection details")
        authentication = self.subparser.add_argument_group("Authentication parameters")
        privilege = self.subparser.add_argument_group("Privilege escalation parameters")
        interpreter = self.subparser.add_argument_group("Python interpreter overrides")
        groups = self.subparser.add_argument_group("Modify groups parameters")

        connection.add_argument(
            "-H",
            "--host",
            type=str,
        )
        connection.add_argument(
            "-P",
            "--port",
            type=str,
        )
        connection.add_argument(
            "-c",
            "--connection",
            type=str,
        )
        authentication.add_argument("-u", "--user", help="User for ansible access")
        authentication.add_argument(
            "-p",
            "--set-password",
            help="Update password for access",
            action="store_true",
        )
        authentication.add_argument(
            "-k",
            "--ssh-private-key-file",
            help="Path to private SSH key",
            action="store_true",
        )
        privilege.add_argument(
            "-b",
            "--set-become-password",
            help="Update password for privilage escalation",
            action="store_true",
        )
        privilege.add_argument("-B", "--become", type=bool)
        privilege.add_argument("-m", "--become-method")
        privilege.add_argument("-U", "--become-user")
        privilege.add_argument(
            "-M",
            "--use-password-as-become-password",
            help="Update password for privilage escalation",
            action="store_true",
        )
        interpreter.add_argument("-I", "--interpreter", default="/usr/bin/python3")
        groups.add_argument(
            "-G",
            "--add-group",
            help="Add groups to host without overriding exist groups",
            action="append",
            type=str,
        )
        groups.add_argument(
            "-R",
            "--rm-group",
            help="Remove groups from host",
            action="append",
            type=str,
        )
        groups.add_argument(
            "--rm-all-groups", help="Remove all groups from host", action="store_true"
        )

    def add_host_to_group(self, group: dict[str, Any], hostname: str) -> None:
        group[hostname] = {}

    def rm_host_from_group(self, group: dict[str, Any], hostname: str) -> None:
        group.pop(hostname)

    def get_host_groupnames(
        self, groups: dict[str, dict[str, dict[str, Any]]], hostname: str
    ) -> list[str]:
        return [
            groupname for groupname, group in groups.items() if hostname in group.keys()
        ]

    def edit_groups_for_host_by_args(
        self, groups: dict[str, dict[str, dict[str, Any]]], hostname: str, args
    ) -> None:
        if args.group is not None and len(args.group) > 0 or args.rm_all_groups:
            existing_groups = self.get_host_groupnames(groups, hostname)
            for group_name in existing_groups:
                self.rm_host_from_group(groups[group_name], hostname)
        for group_name in args.group or []:
            groups[group_name] = groups.get(group_name, {})
            self.add_host_to_group(groups[group_name], hostname)
        for group_name in args.add_group or []:
            groups[group_name] = groups.get(group_name, {})
            self.add_host_to_group(groups.get(group_name, {}), hostname)
        for group_name in args.rm_group or []:
            self.rm_host_from_group(groups.get(group_name, {}), hostname)

    def _clear_empty_groups(self, groups: dict[str, dict[str, dict[str, Any]]]) -> None:
        empty_group_names = [
            group_name for group_name, group in groups.items() if len(group) == 0
        ]
        for group_name in empty_group_names:
            groups.pop(group_name)

    def set_host(self, host: dict[str, Any], args) -> None:
        is_local = args.host in ("127.0.0.1", "localhost") or args.connection == "local"

        keys = [
            "host",
            "port",
            "connection",
            "user",
            "ssh_private_key_file",
            "become_method",
            "become_user",
            "python_interpreter",
        ]
        for key in keys:
            if new_value := getattr(args, key, host.get(f"ansible_{key}", None)):
                host[f"ansible_{key}"] = new_value

        if args.set_become_password and is_local:
            host["ansible_become_pass"] = self._enctypt_password(
                self._get_local_password()
            )
        elif args.set_become_password:
            username = args.hostname or getpass.getuser()
            host["ansible_become_pass"] = self._enctypt_password(
                getpass.getpass(
                    f"Enter the password for {username} on {host['ansible_host']}: "
                )
            )
        if args.use_password_as_become_password:
            host["ansible_become_password"] = "{{ ansible_password }}"
        if args.set_password:
            username = args.hostname or getpass.getuser()
            host["ansible_password"] = self._enctypt_password(
                getpass.getpass(
                    f"Enter the password for {username} on {host['ansible_host']}: "
                )
            )
        new_become_value = getattr(args, "become", host.get("ansible_become", None))
        if new_become_value is not None:
            host["ansible_become"] = new_become_value

    def show_list(
        self,
        hosts: dict[str, dict[str, Any]],
        groups: dict[str, dict[str, Any]],
        filter_group_names: list[str],
    ) -> None:
        for hostname, host in hosts.items():
            mathed_groups = [
                groups.get(group, {}).get(hostname, None) is not None
                for group in filter_group_names or []
            ]
            if filter_group_names and not any(mathed_groups):
                continue
            print(
                hostname,
                f"{host['ansible_connection']}://"
                f"{host.get('user', 'unknown')}@"
                f"{host.get('host', 'unknown')}:"
                f"{host.get('port', 'unknown')} ",
                f"groups: {' '.join(self.get_host_groupnames(groups, hostname))}",
            )

    def run(self, args) -> None:
        content = self._read_inventory(args.inventory)
        hosts = content["all"]["hosts"]
        groups = content["all"]["children"]
        if not args.hostname:
            self.show_list(hosts, groups, args.group)
            exit(0)
        if args.rm:
            hosts.pop(args.hostname)
        hosts[args.hostname] = hosts.get(args.hostname, {})
        self.set_host(hosts[args.hostname], args)
        if len(hosts[args.hostname]) == 0:
            hosts.pop(args.hostname)
        else:
            self.edit_groups_for_host_by_args(groups, args.hostname, args)
        self._clear_empty_groups(groups)
        self._write_inventory(args.inventory, content)

    @classmethod
    def _read_inventory(cls, inventory_path: str) -> dict[str, Any]:
        default_content = {"all": {"hosts": {}, "children": {}}}
        try:
            with open(inventory_path, mode="r") as inventory:
                content = yaml.safe_load(inventory)
                content["all"] = content.get("all", {})
                content["all"]["hosts"] = content["all"].get("hosts", {})
                content["all"]["children"] = content["all"].get("children", {})
                return content
        except FileNotFoundError:
            return default_content

    @classmethod
    def _write_inventory(cls, inventory_path: str, content: dict[str, Any]) -> None:
        with open(inventory_path, mode="w") as inventory:
            yaml.safe_dump(
                content, inventory, default_flow_style=False, sort_keys=False
            )

    @classmethod
    def _enctypt_password(cls, password: str) -> VaultString:
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
    def _get_local_password(cls, username: str | None = None):
        user = username or getpass.getuser()
        while True:
            password = getpass.getpass(
                f"Enter the password for user {user} on your local machine: "
            )
            result = subprocess.run(
                [
                    "su",
                    "-c",
                    '"true"',
                    user,
                ],
                input=password,
                text=True,
                capture_output=True,
            )
            if result.returncode == 0:
                return password
            print("Incorrect password. Repeat")


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


class RunParser(Subparser):
    command = "run"
    help = "Run installation and software configuration"

    def add_args(self) -> None:
        self.subparser.add_argument(
            "--game",
            "-g",
            action="store_true",
            help="Optimize network drivers for gaming",
        )

    def run(self, args) -> None:
        go_to_project()
        run_ansible(game_mode=args.game)


class UpdateParser(Subparser):
    command = "update"
    help = "Update system-setup from github"
    description = None

    def add_args(self) -> None:
        pass

    def run(self, args) -> None:
        pass
        # TODO: implementation


class OpenRepoParser(Subparser):
    command = "open-repo"
    help = "Open repo page"
    description = None

    def run(self, args) -> None:
        webbrowser.open(PROJECT_URL)


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
