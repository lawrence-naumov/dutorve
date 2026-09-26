import subprocess
import sys

from pymodules.base import Subparser
from pymodules.constants import ANSIBLE_DIRECTORY, INVENTORY_FILE


class RunParser(Subparser):
    command = "run"
    help = "Run installation and software configuration"

    def add_args(self) -> None:
        self.subparser.add_argument(
            "--game",
            "-g",
            action="store_true",
            help="Optimize network drivers for gaming",
        )

    def run(self, args) -> None:
        game_mode = args.game
        command = [
            "ansible-playbook",
            "-i",
            INVENTORY_FILE,
            ANSIBLE_DIRECTORY / "setup-playbook.yml",
            "--ask-vault-pass",
        ]

        game_mode_str = "true" if game_mode else "false"
        command.extend(["-e", f"setup_game_mode={game_mode_str}"])

        print("Start to install...")
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError:
            print("Ansible Playbook Error", file=sys.stderr)
            sys.exit(1)
        print("Install success!")
