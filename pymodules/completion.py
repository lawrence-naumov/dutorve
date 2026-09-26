from pathlib import Path
import shlex

import click

from pymodules.cli import cli


def get_commands(command: click.Command) -> dict[str, click.Command]:
    if not isinstance(command, click.Group):
        return {}

    result = {}

    for name in command.list_commands(None):
        subcommand = command.get_command(None, name)

        if subcommand is not None:
            result[name] = subcommand

    return result


def get_options(command: click.Command) -> list[str]:
    result = []

    for param in command.params:
        if not isinstance(param, click.Option):
            continue

        result.extend(param.opts)
        result.extend(param.secondary_opts)

    return result


def get_option_data(command: click.Command) -> list[tuple[str, str]]:
    result = []

    for param in command.params:
        if not isinstance(param, click.Option):
            continue

        options = []

        for option in param.opts:
            options.append(option)

        for option in param.secondary_opts:
            options.append(option)

        help_text = param.help or ""

        for option in options:
            result.append((option, help_text))

    return result


def bash_quote(value: str) -> str:
    return shlex.quote(value)


def generate_bash(path: Path) -> None:
    commands = get_commands(cli)

    lines = [
        "# bash completion for dutorve",
        "",
        "_dutorve() {",
        '    local cur="${COMP_WORDS[COMP_CWORD]}"',
        '    local prev="${COMP_WORDS[COMP_CWORD-1]}"',
        "",
        "    case ${COMP_CWORD} in",
        "        1)",
        "            COMPREPLY=(",
        '                $(compgen -W "',
        f"{' '.join(commands)}",
        "                    -h",
        "                    --help",
        '                " -- "$cur")',
        "            )",
        "            ;;",
        "",
    ]

    for name, command in commands.items():
        options = get_options(command)

        option_words = " ".join(options + ["-h", "--help"])

        lines.extend(
            [
                f"        *)",
                f'            if [[ "${{COMP_WORDS[1]}}" == "{name}" ]]; then',
                f'                local options="{option_words}"',
                "",
                "                COMPREPLY=(",
                '                    $(compgen -W "$options" -- "$cur")',
                "                )",
                "                return",
                "            fi",
                "            ;;",
                "",
            ]
        )

    lines.extend(
        [
            "    esac",
            "}",
            "",
            "complete -F _dutorve dutorve",
            "",
        ]
    )

    path.write_text("\n".join(lines))


def generate_zsh(path: Path) -> None:
    commands = get_commands(cli)

    lines = [
        "#compdef dutorve",
        "",
        "_dutorve() {",
        "    local -a commands",
        "    local -a options",
        "",
        "    if (( CURRENT == 2 )); then",
        "        commands=(",
    ]

    for name, command in commands.items():
        description = command.get_short_help_str()
        description = description.replace("'", "'\\''")

        lines.append(f"            '{name}:{description}'")

    lines.extend(
        [
            "            '-h:Show this message and exit'",
            "            '--help:Show this message and exit'",
            "        )",
            "",
            "        _describe 'command' commands",
            "        return",
            "    fi",
            "",
            "    case ${words[2]} in",
        ]
    )

    for name, command in commands.items():
        lines.extend(
            [
                f"        {name})",
                "            options=(",
            ]
        )

        for option, description in get_option_data(command):
            option_name = option.replace("'", "'\\''")
            description = description.replace("'", "'\\''")

            lines.append(f"                '{option_name}[{description}]'")

        lines.extend(
            [
                "                '-h[Show this message and exit]'",
                "                '--help[Show this message and exit]'",
                "            )",
                "            _describe 'option' options",
                "            ;;",
            ]
        )

    lines.extend(
        [
            "    esac",
            "}",
            "",
            "_dutorve",
            "",
        ]
    )

    path.write_text("\n".join(lines))


def generate_fish(path: Path) -> None:
    commands = get_commands(cli)

    lines = [
        "# fish completion for dutorve",
        "",
        "complete -c dutorve -f "
        '-n "__fish_use_subcommand" '
        "-s h "
        "-l help "
        '-d "Show this message and exit"',
    ]

    for name, command in commands.items():
        description = command.get_short_help_str()

        lines.append(
            f"complete -c dutorve -f "
            f'-n "__fish_use_subcommand" '
            f'-a "{name}" '
            f'-d "{description}"'
        )

    for name, command in commands.items():
        for option, description in get_option_data(command):
            if option.startswith("--"):
                option_name = option[2:]

                lines.append(
                    f"complete -c dutorve "
                    f'-n "__fish_seen_subcommand_from {name}" '
                    f'-l "{option_name}" '
                    f'-d "{description}"'
                )

            elif option.startswith("-") and len(option) == 2:
                option_name = option[1:]

                lines.append(
                    f"complete -c dutorve "
                    f'-n "__fish_seen_subcommand_from {name}" '
                    f'-s "{option_name}" '
                    f'-d "{description}"'
                )

    path.write_text("\n".join(lines) + "\n")


def generate(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    generate_bash(output_dir / "dutorve.bash")
    generate_zsh(output_dir / "_dutorve")
    generate_fish(output_dir / "dutorve.fish")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate static shell completions for dutorve."
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Output directory.",
    )

    args = parser.parse_args()

    generate(args.output)
