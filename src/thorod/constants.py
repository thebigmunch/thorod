import random
import re

from sortedcontainers import SortedDict

UNIX_PATH_RE = re.compile(r'(/(cygdrive/)?)(.*)')
"""Regex pattern matching UNIX-style filepaths."""


DEFAULT_ABBRS = SortedDict(
	{
		'coppersurfer': 'udp://tracker.coppersurfer.tk:6969/announce',
		'cyberia': 'udp://tracker.cyberia.is:6969/announce',
		'demonii': 'udp://open.demonii.si:1337/announce',
		'desync': 'udp://exodus.desync.com:6969/announce',
		'explodie': 'udp://explodie.org:6969/announce',
		'internetwarriors': 'udp://tracker.internetwarriors.net:1337/announce',
		'itzmx': 'udp://tracker1.itzmx.com:8080/announce',
		'leechers-paradise': 'udp://tracker.leechers-paradise.org:6969/announce',
		'opentrackr': 'udp://tracker.opentrackr.org:1337/announce',
		'port443': 'udp://tracker.port443.xyz:6969/announce',
		'rargb': 'udp://9.rarbg.to:2710/announce',
		'stealth': 'udp://open.stealth.si:80/announce',
		'thetracker': 'udp://thetracker.org:80/announce',
		'zer0day': 'udp://tracker.zer0day.to:1337/announce',
	}
)

default_trackers = list(DEFAULT_ABBRS.values())
random.shuffle(default_trackers)

DEFAULT_ABBRS['open'] = default_trackers
DEFAULT_ABBRS['random'] = random.choice(default_trackers)


B = 1024 ** 0
KIB = 1024 ** 1
MIB = 1024 ** 2
GIB = 1024 ** 3
TIB = 1024 ** 4

SYMBOLS = [
	(TIB, 'TiB'),
	(GIB, 'GiB'),
	(MIB, 'MiB'),
	(KIB, 'KiB'),
	(B, 'B'),
]

PIECE_SIZE_VALUES = [
	16 * KIB,
	32 * KIB,
	64 * KIB,
	128 * KIB,
	256 * KIB,
	512 * KIB,
	1 * MIB,
	2 * MIB,
	4 * MIB,
	8 * MIB,
	16 * MIB,
	32 * MIB,
]

PIECE_SIZE_STRINGS = [
	'16k',
	'32k',
	'64k',
	'128k',
	'256k',
	'512k',
	'1m',
	'2m',
	'4m',
	'8m',
	'16m',
	'32m',
	'auto',
]

PIECE_SIZES = dict(zip(PIECE_SIZE_STRINGS, PIECE_SIZE_VALUES))
