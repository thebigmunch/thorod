from collections import ChainMap
from collections.abc import Mapping
from pathlib import Path

import appdirs
from sortedcontainers import SortedDict
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from .__about__ import __author__, __title__
from .constants import DEFAULT_ABBRS
from .utils import DictMixin

COMMAND_KEYS = {
	'abbrs',
	'create',
	'info',
	'magnet',
	'xseed',
}

CONFIG_PATH = Path(appdirs.user_config_dir(__title__, __author__), 'thorod.toml')


def convert_default_keys(item):
	if isinstance(item, Mapping):
		converted = item.__class__()
		for k, v in item.items():
			converted[k.lstrip('-').replace('-', '_')] = convert_default_keys(v)

		return converted
	else:
		return item


def get_defaults(command):
	config_defaults = read_config_file().get('defaults')
	print(config_defaults)
	defaults = DictMixin()

	if config_defaults:
		defaults.update(
			(k, v)
			for k, v in config_defaults.items()
			if k not in COMMAND_KEYS
		)

		if command in config_defaults:
			defaults.update(
				(k, v)
				for k, v in config_defaults[command[0]].items()
				if k not in COMMAND_KEYS
			)

	return convert_default_keys(defaults)


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
