import getpass
import subprocess
from typing import Any

import click
import yaml

from pymodules.colors import ColoredCommand

from pymodules.constants import INVENTORY_FILE


class VaultString(str):
    @staticmethod
    def representer(dumper, data):
        return dumper.represent_scalar("!vault", data, style="|")

    @classmethod
    def constructor(cls, loader, node):
        return cls(loader.construct_scalar(node))


yaml.SafeDumper.add_representer(VaultString, VaultString.representer)
yaml.SafeLoader.add_constructor("!vault", VaultString.constructor)


class InventoryManager:
    def add_host_to_group(
        self,
        group: dict[str, Any],
        hostname: str,
    ) -> None:
        group[hostname] = {}

    def rm_host_from_group(
        self,
        group: dict[str, Any],
        hostname: str,
    ) -> None:
        group.pop(hostname, None)

    def get_host_groupnames(
        self,
        groups: dict[str, dict[str, dict[str, Any]]],
        hostname: str,
    ) -> list[str]:
        return [groupname for groupname, group in groups.items() if hostname in group]

    def edit_groups_for_host(
        self,
        groups: dict[str, dict[str, dict[str, Any]]],
        hostname: str,
        args: dict[str, Any],
    ) -> None:
        if args["group"] or args["rm_all_groups"]:
            existing_groups = self.get_host_groupnames(groups, hostname)

            for group_name in existing_groups:
                self.rm_host_from_group(
                    groups[group_name],
                    hostname,
                )

        for group_name in args["group"]:
            groups.setdefault(group_name, {})
            self.add_host_to_group(
                groups[group_name],
                hostname,
            )

        for group_name in args["add_group"]:
            groups.setdefault(group_name, {})
            self.add_host_to_group(
                groups[group_name],
                hostname,
            )

        for group_name in args["rm_group"]:
            self.rm_host_from_group(
                groups.get(group_name, {}),
                hostname,
            )

    def clear_empty_groups(
        self,
        groups: dict[str, dict[str, dict[str, Any]]],
    ) -> None:
        for group_name in list(groups):
            if not groups[group_name]:
                groups.pop(group_name)

    def set_host(
        self,
        host_data: dict[str, Any],
        args: dict[str, Any],
    ) -> None:
        is_local = (
            args["host"] in ("127.0.0.1", "localhost") or args["connection"] == "local"
        )

        values = {
            "host": args["host"],
            "port": args["port"],
            "connection": args["connection"],
            "user": args["user"],
            "ssh_private_key_file": args["ssh_private_key_file"],
            "become_method": args["become_method"],
            "become_user": args["become_user"],
            "python_interpreter": args["interpreter"],
        }

        for key, value in values.items():
            if value:
                host_data[f"ansible_{key}"] = value

        if args["set_become_password"]:
            if is_local:
                password = self.get_local_password()
            else:
                username = args["hostname"] or getpass.getuser()
                password = getpass.getpass(f"Enter the password for {username}: ")

            host_data["ansible_become_pass"] = self.encrypt_password(password)

        if args["use_password_as_become_password"]:
            host_data["ansible_become_password"] = "{{ ansible_password }}"

        if args["set_password"]:
            username = args["hostname"] or getpass.getuser()
            password = getpass.getpass(
                f"Enter the password for {username} on {host_data['ansible_host']}: "
            )
            host_data["ansible_password"] = self.encrypt_password(password)

        if args["become"] is not None:
            host_data["ansible_become"] = args["become"]

    def show_list(
        self,
        hosts: dict[str, dict[str, Any]],
        groups: dict[str, dict[str, Any]],
        filter_group_names: tuple[str, ...],
    ) -> None:
        for hostname, host in hosts.items():
            if filter_group_names:
                host_groups = self.get_host_groupnames(
                    groups,
                    hostname,
                )

                if not any(group in host_groups for group in filter_group_names):
                    continue

            click.echo(
                f"{hostname} "
                f"{host.get('ansible_connection', 'unknown')}://"
                f"{host.get('ansible_user', 'unknown')}@"
                f"{host.get('ansible_host', 'unknown')}:"
                f"{host.get('ansible_port', 'unknown')} "
                f"groups: {' '.join(self.get_host_groupnames(groups, hostname))}"
            )

    def run(self, args: dict[str, Any]) -> None:
        content = self.read_inventory(args["inventory"])

        hosts = content["all"]["hosts"]
        groups = content["all"]["children"]

        if not args["hostname"]:
            self.show_list(hosts, groups, args["group"])
            return

        hostname = args["hostname"]

        if args["rm"]:
            hosts.pop(hostname, None)

        hosts[hostname] = hosts.get(hostname, {})

        self.set_host(hosts[hostname], args)

        if not hosts[hostname]:
            hosts.pop(hostname)
        else:
            self.edit_groups_for_host(
                groups,
                hostname,
                args,
            )

        self.clear_empty_groups(groups)
        self.write_inventory(args["inventory"], content)

    @staticmethod
    def read_inventory(
        inventory_path: str,
    ) -> dict[str, Any]:
        default_content = {
            "all": {
                "hosts": {},
                "children": {},
            }
        }

        try:
            with open(inventory_path, "r") as inventory:
                content = yaml.safe_load(inventory) or {}

        except FileNotFoundError:
            return default_content

        content.setdefault("all", {})
        content["all"]["hosts"] = content["all"].get("hosts", {}) or {}
        content["all"]["children"] = content["all"].get("children", {}) or {}

        return content

    @staticmethod
    def write_inventory(
        inventory_path: str,
        content: dict[str, Any],
    ) -> None:
        with open(inventory_path, "w") as inventory:
            yaml.safe_dump(
                content,
                inventory,
                default_flow_style=False,
                sort_keys=False,
            )

    @staticmethod
    def encrypt_password(password: str) -> VaultString:
        result = subprocess.run(
            [
                "ansible-vault",
                "encrypt_string",
                "--stdin-name=ansible_become_pass",
            ],
            input=password,
            text=True,
            capture_output=True,
            check=True,
        )

        return yaml.safe_load(result.stdout)["ansible_become_pass"]

    @staticmethod
    def get_local_password(
        username: str | None = None,
    ) -> str:
        user = username or getpass.getuser()

        while True:
            password = getpass.getpass(
                f"Enter the password for user {user} on your local machine: "
            )

            result = subprocess.run(
                ["su", "-c", "true", user],
                input=password,
                text=True,
                capture_output=True,
            )

            if result.returncode == 0:
                return password

            click.echo("Incorrect password. Repeat")


@click.command(
    "inventory",
    cls=ColoredCommand,
    help="Manage hosts and groups in the Ansible inventory.",
)
@click.argument(
    "hostname",
    required=False,
    metavar="HOST",
)
@click.option(
    "-i",
    "--inventory",
    "inventory_path",
    type=click.Path(path_type=str),
    default=str(INVENTORY_FILE),
    show_default=True,
    metavar="FILE",
    help="Path to the Ansible inventory file.",
)
@click.option(
    "--rm",
    is_flag=True,
    help="Remove the specified host from the inventory.",
)
@click.option(
    "-g",
    "--group",
    multiple=True,
    metavar="GROUP",
    help="Replace the host's groups with the specified groups.",
)
@click.option(
    "-H",
    "--host",
    metavar="HOST",
    help="Remote host address or hostname.",
)
@click.option(
    "-P",
    "--port",
    metavar="PORT",
    help="SSH port.",
)
@click.option(
    "-c",
    "--connection",
    metavar="TYPE",
    help="Ansible connection type, for example: ssh or local.",
)
@click.option(
    "-u",
    "--user",
    metavar="USER",
    help="Remote user used by Ansible.",
)
@click.option(
    "-p",
    "--set-password",
    is_flag=True,
    help="Prompt for and update the Ansible connection password.",
)
@click.option(
    "-k",
    "--ssh-private-key-file",
    type=click.Path(path_type=str),
    metavar="FILE",
    help="Path to the SSH private key.",
)
@click.option(
    "-b",
    "--set-become-password",
    is_flag=True,
    help="Prompt for and update the privilege escalation password.",
)
@click.option(
    "-B",
    "--become/--no-become",
    default=None,
    help="Enable or disable Ansible privilege escalation.",
)
@click.option(
    "-m",
    "--become-method",
    metavar="METHOD",
    help="Privilege escalation method, for example: sudo.",
)
@click.option(
    "-U",
    "--become-user",
    metavar="USER",
    help="User to become when privilege escalation is enabled.",
)
@click.option(
    "-M",
    "--use-password-as-become-password",
    is_flag=True,
    help="Use the Ansible connection password as the privilege escalation password.",
)
@click.option(
    "-I",
    "--interpreter",
    default="/usr/bin/python3",
    show_default=True,
    metavar="PATH",
    help="Path to the Python interpreter on the managed host.",
)
@click.option(
    "-G",
    "--add-group",
    multiple=True,
    metavar="GROUP",
    help="Add the host to a group without changing existing groups.",
)
@click.option(
    "-R",
    "--rm-group",
    multiple=True,
    metavar="GROUP",
    help="Remove the host from a group.",
)
@click.option(
    "--rm-all-groups",
    is_flag=True,
    help="Remove the host from all groups.",
)
def inventory(
    hostname: str | None,
    inventory_path: str,
    rm: bool,
    group: tuple[str, ...],
    host: str | None,
    port: str | None,
    connection: str | None,
    user: str | None,
    set_password: bool,
    ssh_private_key_file: str | None,
    set_become_password: bool,
    become: bool | None,
    become_method: str | None,
    become_user: str | None,
    use_password_as_become_password: bool,
    interpreter: str,
    add_group: tuple[str, ...],
    rm_group: tuple[str, ...],
    rm_all_groups: bool,
) -> None:
    """Manage Ansible inventory."""

    args = {
        "hostname": hostname,
        "inventory": inventory_path,
        "rm": rm,
        "group": group,
        "host": host,
        "port": port,
        "connection": connection,
        "user": user,
        "set_password": set_password,
        "ssh_private_key_file": ssh_private_key_file,
        "set_become_password": set_become_password,
        "become": become,
        "become_method": become_method,
        "become_user": become_user,
        "use_password_as_become_password": use_password_as_become_password,
        "interpreter": interpreter,
        "add_group": add_group,
        "rm_group": rm_group,
        "rm_all_groups": rm_all_groups,
    }

    InventoryManager().run(args)
