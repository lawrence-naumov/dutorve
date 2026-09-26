import os
import subprocess


class Installer:
    @staticmethod
    def _is_root() -> bool:
        return os.geteuid() == 0

    def create_system_symlink():
        commands = [
            ["chmod", "755", PROJECT_DIRECTORY / "configure.py"],
            [
                "ln",
                "-fs",
                PROJECT_DIRECTORY / "configure.py",
                BIN_DIRECTORY / COMMAND_NAME,
            ],
            ["chown", "-h", "root:root", BIN_DIRECTORY / COMMAND_NAME],
        ]

        if not is_root():
            commands = [["sudo"] + command for command in commands]

        for command in commands:
            subprocess.run(command, check=True)

    def install_project():
        PROJECT_DIRECTORY.parent.mkdir(exist_ok=True, parents=True)
        os.chdir(PROJECT_DIRECTORY.parent)
        # TODO: Make better exceptions for making project parent directory
        exceptions = []
        # TODO: check is git available
        for url in SSH_URL, PROJECT_URL:
            try:
                subprocess.run(
                    ["git", "clone", url, PROJECT_DIRECTORY.name], check=True
                )
            except subprocess.CalledProcessError as exc:
                exceptions.append(exc)
            else:
                if ask("Create system symlink?", default=True):
                    create_system_symlink()
                return
        for exc in exceptions:
            traceback.print_exception(exc)
        print("Failed to install project with exceptions above", file=sys.stderr)

    def go_to_project():
        try:
            os.chdir(PROJECT_DIRECTORY)
        except FileNotFoundError:
            if ask("Project directory was not found. Do you want to install?"):
                install_project()
                os.chdir(PROJECT_DIRECTORY)
            else:
                exit(1)
