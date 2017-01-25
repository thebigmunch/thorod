import os
import random
from collections import ChainMap

import appdirs
import toml
from sortedcontainers import SortedDict

from .__about__ import __author__, __title__

CONFIG_DIR = appdirs.user_config_dir(__title__, __author__)
CONFIG_FILE = os.path.join(CONFIG_DIR, 'thorod.toml')

DEFAULT_ABBRS = SortedDict({
	'coppersurfer': 'udp://tracker.coppersurfer.tk:6969/announce',
	'demonii': 'udp://open.demonii.com:1337',
	'desync': 'udp://exodus.desync.com:6969',
	'explodie': 'udp://explodie.org:6969',
	'internetwarriors': 'udp://tracker.internetwarriors.net:1337/announce',
	'leechers-paradise': 'udp://tracker.leechers-paradise.org:6969/announce',
	'mgtracker': 'udp://mgtracker.org:6969/announce',
	'opentrackr': 'udp://tracker.opentrackr.org:1337',
	'pirateparty': 'udp://tracker.pirateparty.gr:6969/announce',
	'sktorrent': 'udp://tracker.sktorrent.net:6969/announce',
	'zer0day': 'udp://tracker.zer0day.to:1337/announce'
})

default_trackers = list(DEFAULT_ABBRS.values())
random.shuffle(default_trackers)

DEFAULT_ABBRS['open'] = default_trackers
DEFAULT_ABBRS['random'] = random.choice(default_trackers)


def get_config():
	config = read_config_file()

	return config


def read_config_file():
	try:
		with open(CONFIG_FILE) as conf:
			config = toml.load(conf, SortedDict)
	except FileNotFoundError:
		config = SortedDict()

	if 'trackers' not in config:
		config['trackers'] = SortedDict()

	write_config_file(config)

	return config


def write_config_file(config):
	os.makedirs(CONFIG_DIR, exist_ok=True)

	with open(CONFIG_FILE, 'w') as conf:
		toml.dump(config, conf)


ABBRS = ChainMap(DEFAULT_ABBRS, get_config()['trackers'])
