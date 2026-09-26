import os
import pathlib


ETC_DIR = pathlib.Path(os.getenv("DUTORVE_ETC_DIR", "./"))
OPT_DIR = pathlib.Path(os.getenv("DUTORVE_OPT_DIR", "./"))
INVENTORY_FILE = ETC_DIR / "inventory.yml"
ANSIBLE_DIRECTORY = OPT_DIR / "ansible"
