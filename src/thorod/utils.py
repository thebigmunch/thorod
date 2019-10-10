import os
import random
import string
from hashlib import sha1

from . import bencode
from .constants import PIECE_SIZE_VALUES


def calculate_data_size(files):
	"""Calculate the total size of the input data."""

	return sum(os.path.getsize(f) for f in files)


def calculate_piece_size(data_size, *, threshold=2000):
	for piece_size in PIECE_SIZE_VALUES:
		if data_size / piece_size < threshold:
			break

	return piece_size


def calculate_torrent_size(torrent_info):
	"""Calculate the total size of the files in a torrent."""

	files = torrent_info.get('info').get('files') or [
		torrent_info['info']
	]

	return sum(f['length'] for f in files)


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
