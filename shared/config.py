import os
import pathlib

from poyo import parse_string
from poyo.utils import read_unicode_file

CURRENT_FILE = pathlib.Path(__file__).resolve()

PROJECT_ROOT = CURRENT_FILE.parent.parent

CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_configuration(path: str | pathlib.Path):
    strings = read_unicode_file(path)
    configuration = parse_string(strings)
    flatten_and_export(configuration)


def flatten_and_export(d: dict, prefix: str = ""):
    for key, value in d.items():
        full_key = f"{prefix}{key}".upper()
        if isinstance(value, dict):
            flatten_and_export(value, prefix=f"{full_key}_")
        else:
            os.environ[full_key] = str(value)


class Configuration:

    def __init__(self):
        load_configuration(CONFIG_PATH)

    def __getattr__(self, item: str):
        value = os.getenv(item)
        if value is None:
            raise NotFoundEnvironment(item)
        if item == "Debug":
            return value.lower() == "true"
        return value


class NotFoundEnvironment(Exception):
    def __init__(self, field: str):
        self.message = f"Unknown environment variable: '{field}' not found in environment variables."
        super().__init__(self.message)
