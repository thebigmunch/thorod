import os
import random
import string
from collections.abc import MutableMapping
from hashlib import sha1
from pathlib import Path

import pprintpp

from . import bencode
from .constants import (
	PIECE_SIZE_VALUES,
	SYMBOLS,
	UNIX_PATH_RE,
)


class DictMixin(MutableMapping):
	def __getattr__(self, attr):
		try:
			return self.__getitem__(attr)
		except KeyError:
			raise AttributeError(attr) from None

	def __setattr__(self, attr, value):
		self.__setitem__(attr, value)

	def __delattr__(self, attr):
		try:
			return self.__delitem__(attr)
		except KeyError:
			raise AttributeError(attr) from None

	def __getitem__(self, key):
		return self.__dict__[key]

	def __setitem__(self, key, value):
		self.__dict__[key] = value

	def __delitem__(self, key):
		del self.__dict__[key]

	def __missing__(self, key):
		return KeyError(key)

	def __iter__(self):
		return iter(self.__dict__)

	def __len__(self):
		return len(self.__dict__)

	def __repr__(self, repr_dict=None):
		return f"<{self.__class__.__name__} ({pprintpp.pformat(self.__dict__)})>"

	def items(self):
		return self.__dict__.items()

	def keys(self):
		return self.__dict__.keys()

	def values(self):
		return self.__dict__.values()


def calculate_data_size(files):
	"""Calculate the total size of the input data."""

	return sum(os.path.getsize(f) for f in files)


def calculate_piece_size(data_size):
	for piece_size in PIECE_SIZE_VALUES:
		if data_size / piece_size < 2000:
			break

	return piece_size


def calculate_torrent_size(torrent_info):
	"""Calculate the total size of the files in a torrent."""

	files = torrent_info.get('info').get('files') or [
		torrent_info['info']
	]

	return sum(f['length'] for f in files)


def convert_unix_path(filepath):
	"""Convert Unix filepath string from Cygwin et al to Windows format.

	Parameters:
		filepath (str): A filepath string.

	Returns:
		str: A filepath string in Windows format.

	Raises:
		FileNotFoundError
		subprocess.CalledProcessError
	"""

	match = UNIX_PATH_RE.match(filepath)
	if not match:
		return Path(filepath.replace('/', r'\\'))

	parts = match.group(3).split('/')
	parts[0] = f"{parts[0].upper()}:/"

	return Path(*parts)


def generate_unique_string():
	"""Generate a random string to make a torrent's infohash unique."""

	return ''.join(
		random.choice(string.ascii_letters + string.digits)
		for x in range(32)
	)


def get_file_path(filepath, basedir):
	"""Get all parts of the file path relative to the base directory of the torrent."""

	return list(filepath.relative_to(basedir).parts)


def hash_info_dict(info_dict):
	return sha1(bencode.dumps(info_dict)).hexdigest()


def humanize_size(size, precision=0, **kwargs):
	"""Convert size in bytes to a binary size string.

	Parameters:
		size (int): Data size in bytes.

		precision (int): Number of decimal places to return.

	Returns:
		str: File size string with appropriate unit.
	"""

	for multiple, symbol in SYMBOLS:
		if size >= multiple:
			break

	return f'{size / multiple:.{precision}f} {symbol}'


def walk_depth(path, max_depth=float('inf')):
	"""Walk a directory tree with configurable depth.

	Parameters:
		path (str): A directory path to walk.

		max_depth (int): The depth in the directory tree to walk.
			A depth of '0' limits the walk to the top directory.
			Default: No limit.

	Yields:
		tuple: A 3-tuple ``(root, dirs, files)`` same as :func:`os.walk`.
	"""

	path = os.path.abspath(path)

	start_level = path.count(os.path.sep)

	for dir_entry in os.walk(path):
		root, dirs, _ = dir_entry
		level = root.count(os.path.sep) - start_level

		yield dir_entry

		if level >= max_depth:
			dirs[:] = []
