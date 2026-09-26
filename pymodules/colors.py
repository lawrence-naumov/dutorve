import click


def color_option(opts: str) -> str:
    """
    Color option names and their metavars separately.

    Example:
        -R, --rm-group GROUP
              ^^^^^^^^^^
    """
    parts = opts.split()

    result = []

    for part in parts:
        if part.startswith("-"):
            result.append(click.style(part, fg="green", bold=True))
        else:
            result.append(click.style(part, fg="cyan", bold=True))

    return " ".join(result)


def format_options(command, ctx, formatter) -> None:
    options = []

    for param in command.get_params(ctx):
        rv = param.get_help_record(ctx)

        if rv is None:
            continue

        opts, help_text = rv

        options.append(
            (
                color_option(opts),
                help_text,
            )
        )

    if not options:
        return

    with formatter.section(click.style("Options", fg="yellow", bold=True)):
        formatter.write_dl(options)


class ColoredCommand(click.Command):
    def format_usage(self, ctx, formatter):
        pieces = self.collect_usage_pieces(ctx)

        formatter.write(click.style("Usage:", fg="green", bold=True))

        formatter.write(f" {click.style(ctx.command_path, fg='cyan', bold=True)}")

        if pieces:
            formatter.write(" " + " ".join(pieces))

        formatter.write("\n")

    def format_options(self, ctx, formatter):
        format_options(self, ctx, formatter)


class ColoredGroup(click.Group):
    command_class = ColoredCommand

    def format_usage(self, ctx, formatter):
        pieces = self.collect_usage_pieces(ctx)

        formatter.write(click.style("Usage:", fg="green", bold=True))

        formatter.write(f" {click.style(ctx.command_path, fg='cyan', bold=True)}")

        if pieces:
            formatter.write(" " + " ".join(pieces))

        formatter.write("\n")

    def format_options(self, ctx, formatter):
        format_options(self, ctx, formatter)

    def format_commands(self, ctx, formatter):
        commands = []

        for name in self.list_commands(ctx):
            command = self.get_command(ctx, name)

            if command is None:
                continue

            commands.append(
                (
                    click.style(name, fg="cyan", bold=True),
                    command.get_short_help_str(),
                )
            )

        if not commands:
            return

        with formatter.section(click.style("Commands", fg="yellow", bold=True)):
            formatter.write_dl(commands)
