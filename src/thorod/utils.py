import os
import random
import string
import subprocess
from hashlib import sha1

from . import bencode
from .constants import PIECE_SIZE_VALUES, SYMBOLS


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

	files = torrent_info.get('info').get('files') or [torrent_info['info']]

	return sum(f['length'] for f in files)


def convert_cygwin_path(path):
	"""Convert Unix path string from Cygwin to Windows format.

	Parameters:
		path (str): A path string.

	Returns:
		str: A path string in Windows format.

	Raises:
		FileNotFoundError
		:exc:`subprocess.CalledProcessError`
	"""

	try:
		win_path = subprocess.check_output(["cygpath", "-aw", path], universal_newlines=True).strip()
	except (FileNotFoundError, subprocess.CalledProcessError):
		raise subprocess.CalledProcessError("Call to cygpath failed.")

	return win_path


def generate_unique_string():
	"""Generate a random string to make a torrent's infohash unique."""

	return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32))


def get_files(path, max_depth=float('inf')):
	"""Create a list of files from given path."""

	if os.path.isfile(path):
		yield path
	elif os.path.isdir(path):
		for root, _, files in walk_depth(path, max_depth=max_depth):
			for f in files:
				yield os.path.join(root, f)


def get_file_path(file, basedir):
	"""Get all parts of the file path relative to the base directory of the torrent."""

	head = os.path.relpath(file, basedir)
	parts = []

	while head:
		head, tail = os.path.split(head)
		parts.insert(0, tail)

	return parts


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
