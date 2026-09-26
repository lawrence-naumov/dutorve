import click

from pymodules.cli import ColoredGroup
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


cli.add_command(run)
cli.add_command(inventory)


def main():
    cli(prog_name="dutorve")


if __name__ == "__main__":
    main()
