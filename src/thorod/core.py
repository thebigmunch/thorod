import functools
import os
import random
from hashlib import md5, sha1

from tqdm import tqdm

from . import bencode
from .utils import (
	calculate_torrent_size, generate_unique_string, get_file_path, hash_info_dict, humanize_size
)

tqdm.format_sizeof = functools.partial(humanize_size, precision=2)


def create_dir_info_dict(files, data_size, piece_size, private, source, include_md5, show_progress=True):
	base_path = os.path.commonpath(files)

	info_dict = {}
	file_infos = []
	data = bytes()
	pieces = bytes()

	if show_progress:
		print("Hashing files:\n")
		progress_bar = tqdm(
			total=data_size, unit='', unit_scale=True,
			leave=True, dynamic_ncols=True,
			bar_format='{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} [{remaining}  {rate_fmt}]'
		)

	for file in files:
		file_dict = {}
		length = 0

		md5sum = md5() if include_md5 else None

		with open(file, 'rb') as f:
			while True:
				piece = f.read(piece_size)

				if not piece:
					break

				length += len(piece)

				data += piece

				if len(data) >= piece_size:
					pieces += sha1(data[:piece_size]).digest()
					data = data[piece_size:]

				if include_md5:
					md5sum.update(piece)

				if show_progress:
					progress_bar.update(len(piece))

		file_dict['length'] = length
		file_dict['path'] = get_file_path(file, base_path)

		if include_md5:
			file_dict['md5sum'] = md5sum.hexdigest()

		file_infos.append(file_dict)

	if show_progress:
		progress_bar.close()

	if len(data) > 0:
		pieces += sha1(data).digest()

	info_dict['files'] = file_infos
	info_dict['name'] = os.path.basename(base_path)
	info_dict['pieces'] = pieces
	info_dict['piece length'] = piece_size
	info_dict['salt'] = generate_unique_string()

	info_dict['private'] = 1 if private else 0

	if source:
		info_dict['source'] = source

	return info_dict


def create_file_info_dict(files, data_size, piece_size, private, source, include_md5, show_progress=True):
	info_dict = {}
	pieces = bytes()
	length = 0

	md5sum = md5() if include_md5 else None

	if show_progress:
		print("Hashing file:\n")
		progress_bar = tqdm(
			total=data_size, unit='', unit_scale=True,
			leave=True, dynamic_ncols=True,
			bar_format='{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} [{remaining}  {rate_fmt}]'
		)

	with open(files[0], 'rb') as f:
		while True:
			piece = f.read(piece_size)

			if not piece:
				break

			length += len(piece)

			pieces += sha1(piece).digest()

			if include_md5:
				md5sum.update(piece)

			if show_progress:
				progress_bar.update(len(piece))

	if show_progress:
		progress_bar.close()

	info_dict['name'] = os.path.basename(files[0])
	info_dict['length'] = length
	info_dict['pieces'] = pieces
	info_dict['piece length'] = piece_size
	info_dict['salt'] = generate_unique_string()

	info_dict['private'] = 1 if private else 0

	if source:
		info_dict['source'] = source

	if include_md5:
		info_dict['md5sum'] = md5sum.hexdigest()

	return info_dict


def generate_magnet_link(torrent_info, torrent_file):
	torrent_name = torrent_file.replace('.torrent', '')

	info_hash = hash_info_dict(torrent_info['info'])
	data_size = calculate_torrent_size(torrent_info)

	magnet_link = f'magnet:?dn={torrent_name}&xt=urn:btih:{info_hash}&xl={data_size}'

	if 'announce-list' in torrent_info:
		for tier in torrent_info['announce-list']:
			magnet_link += f'&tr={random.choice(tier)}'
	elif 'announce' in torrent_info:
		magnet_link += f'&tr={torrent_info["announce"]}'

	return magnet_link


def read_torrent_file(filepath):
	try:
		with open(filepath, 'rb') as f:
			torrent_info = bencode.load(f)
	except FileNotFoundError:
		raise FileNotFoundError(f"{filepath!r} not found.")
	except TypeError:
		raise TypeError(f"Could not parse {filepath!r}.")

	return torrent_info


def write_torrent_file(filepath, torrent_info):
	with open(filepath, 'wb') as f:
		bencode.dump(torrent_info, f)
