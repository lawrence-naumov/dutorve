import sys


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
