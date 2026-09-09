#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import traceback
import pathlib
import webbrowser


BIN_DIRECTORY = pathlib.Path("/usr/local/bin")
PROJECT_URL = "https://github.com/prostoLavr/ansible-system-setup.git"
SSH_URL = "git@github.com:prostoLavr/ansible-system-setup.git"
PROJECT_DIRECTORY = pathlib.Path.home() / ".test-system-setup"
INVENTORY_FILE = pathlib.Path("inventory.yml")
VAULT_PASS_FILE = pathlib.Path(".vault_pass")
COMMAND_NAME = "test-system-setup"


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
    command = ["ansible-playbook", "setup-playbook.yml"]

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


def main():
    go_to_project()
    parser = argparse.ArgumentParser(
        description="Lawrence's system setup CLI tool",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=False, help="command")
    help_parser = subparsers.add_parser(
        "help", help="Show help message for any command"
    )
    help_parser.add_argument(
        "help_command",
        help="Show help for specific command",
        metavar="command",
        nargs="?",
    )

    run_parser = subparsers.add_parser(
        "run", help="Run installation and software configuration"
    )
    run_parser.add_argument(
        "--game",
        "-g",
        action="store_true",
        help="Optimize network drivers for gaming",
    )

    subparsers.add_parser("update", help="Update system-setup from github")
    subparsers.add_parser("open-repo", help="Open repo page")
    subparsers.add_parser("workdir", help="Show project working directory")
    subparsers.add_parser(
        "recreate-inventory",
        help="Recreate ansible inventory file",
        description="Use when you chanched password or forgot the inventory file password",
    )

    args = parser.parse_args()

    if args.command == "help" or not args.command:
        if args.help_command:
            try:
                subparsers.choices[args.help_command].print_help()
            except KeyError:
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
    if args.command == "open-repo":
        webbrowser.open(PROJECT_URL)
    if args.command == "workdir":
        print(PROJECT_DIRECTORY)
    if args.command == "install":
        run_ansible(game_mode=args.game)


if __name__ == "__main__":
    main()
