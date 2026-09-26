import tomllib
import pathlib


class Configuration:
    def __init__(self, config_path: pathlib.Path):
        with config_path.open("rb") as config_file:
            config = tomllib.load(config_file)
        self.config = config

    @property
    def bin_directory(self) -> pathlib.Path:
        return pathlib.Path(self.config["bin_directory"])
    
    @property
    def 


BIN_DIRECTORY = pathlib.Path("/usr/local/bin")
PROJECT_URL = "https://github.com/prostoLavr/ansible-system-setup.git"
SSH_URL = "git@github.com:prostoLavr/ansible-system-setup.git"
PROJECT_DIRECTORY = pathlib.Path.home() / ".test-system-setup"
INVENTORY_FILE = pathlib.Path("inventory.yml")
VAULT_PASS_FILE = pathlib.Path(".vault_pass")
COMMAND_NAME = "test-system-setup"
