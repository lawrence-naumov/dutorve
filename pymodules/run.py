import subprocess

import click

from pymodules.colors import ColoredCommand
from pymodules.constants import ANSIBLE_DIRECTORY, INVENTORY_FILE


@click.command(
    "run",
    cls=ColoredCommand,
)
@click.option(
    "--game",
    "-g",
    is_flag=True,
    help="Optimize network drivers for gaming.",
)
def run(game: bool) -> None:
    """Run installation and software configuration."""

    command = [
        "ansible-playbook",
        "-i",
        str(INVENTORY_FILE),
        str(ANSIBLE_DIRECTORY / "setup-playbook.yml"),
        "--ask-vault-pass",
        "-e",
        f"setup_game_mode={'true' if game else 'false'}",
    ]

    click.echo("Start to install...")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        click.echo("Ansible Playbook Error", err=True)
        raise click.exceptions.Exit(1)

    click.echo("Install success!")
