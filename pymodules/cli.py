import click


class ColoredGroup(click.Group):
    def format_usage(self, ctx, formatter):
        pieces = self.collect_usage_pieces(ctx)

        formatter.write(click.style("Usage:", fg="green", bold=True))
        formatter.write(f" {click.style(ctx.command_path, fg='cyan', bold=True)}")

        if pieces:
            formatter.write(" " + " ".join(pieces))

        formatter.write("\n")

    def format_commands(self, ctx, formatter):
        commands = []

        for name in self.list_commands(ctx):
            command = self.get_command(ctx, name)

            if command is None:
                continue

            commands.append(
                (
                    click.style(
                        name,
                        fg="cyan",
                        bold=True,
                    ),
                    command.get_short_help_str(),
                )
            )

        if not commands:
            return

        with formatter.section(click.style("Commands", fg="yellow", bold=True)):
            formatter.write_dl(commands)
