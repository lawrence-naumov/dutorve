import click

from pymodules.colors import ColoredGroup
from pymodules.inventory import inventory
from pymodules.run import run


@click.group(
    cls=ColoredGroup,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
def cli():
    """Configure hosts with prepared ansible playbooks."""


cli.add_command(inventory)
cli.add_command(run)
