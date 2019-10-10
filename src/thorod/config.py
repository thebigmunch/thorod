from collections import ChainMap
from pathlib import Path

import appdirs
from sortedcontainers import SortedDict
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from .__about__ import __author__, __title__
from .constants import DEFAULT_ABBRS

CONFIG_PATH = Path(appdirs.user_config_dir(__title__, __author__), 'thorod.toml')


def read_config_file():
	config_file = TOMLFile(CONFIG_PATH)
	try:
		config = config_file.read()
	except FileNotFoundError:
		config = TOMLDocument()

	if 'trackers' not in config:
		config['trackers'] = SortedDict()

	write_config_file(config)

	return config


def write_config_file(config):
	CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
	CONFIG_PATH.touch()

	config_file = TOMLFile(CONFIG_PATH)
	config_file.write(config)


ABBRS = ChainMap(DEFAULT_ABBRS, read_config_file()['trackers'])
