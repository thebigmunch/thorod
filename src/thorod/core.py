import functools
import math
import os
import platform
import random
from hashlib import md5, sha1
from pathlib import Path

import crayons
import pendulum
from sortedcontainers import SortedDict
from tqdm import tqdm

from . import bencode
from .config import CONFIG_PATH
from .constants import DEFAULT_ABBRS
from .utils import (
	calculate_torrent_size,
	generate_unique_string,
	get_file_path,
	hash_info_dict,
	humanize_size,
)

tqdm.format_sizeof = functools.partial(humanize_size, precision=2)


def create_dir_info_dict(
	files,
	data_size,
	piece_size,
	private,
	source,
	include_md5,
	show_progress=True,
):
	base_path = Path(os.path.commonpath(files))

	info_dict = SortedDict()
	file_infos = []
	data = bytes()
	pieces = bytes()

	if show_progress:
		print("\n")
		progress_bar = tqdm(
			total=data_size,
			unit='',
			unit_scale=True,
			leave=True,
			dynamic_ncols=True,
			bar_format='{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} [{remaining} {rate_fmt}]',
		)

	for file_ in files:
		file_dict = SortedDict()
		length = 0

		md5sum = md5() if include_md5 else None

		with open(file_, 'rb') as f:
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
		file_dict['path'] = get_file_path(file_, base_path)

		if include_md5:
			file_dict['md5sum'] = md5sum.hexdigest()

		file_infos.append(file_dict)

	if show_progress:
		progress_bar.close()

	if len(data) > 0:
		pieces += sha1(data).digest()

	info_dict['files'] = file_infos
	info_dict['name'] = base_path.name
	info_dict['pieces'] = pieces
	info_dict['piece length'] = piece_size
	info_dict['salt'] = generate_unique_string()

	info_dict['private'] = 1 if private else 0

	if source:
		info_dict['source'] = source

	return info_dict


def create_file_info_dict(
	files,
	data_size,
	piece_size,
	private,
	source,
	include_md5,
	show_progress=True,
):
	info_dict = SortedDict()
	pieces = bytes()
	length = 0

	md5sum = md5() if include_md5 else None

	if show_progress:
		print("\n")
		progress_bar = tqdm(
			total=data_size,
			unit='',
			unit_scale=True,
			leave=True,
			dynamic_ncols=True,
			bar_format='{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} [{remaining} {rate_fmt}]',
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

	info_dict['name'] = files[0].name
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


def filter_dates(
	filepaths,
	*,
	created_in=None,
	created_on=None,
	created_before=None,
	created_after=None,
	modified_in=None,
	modified_on=None,
	modified_before=None,
	modified_after=None
):
	matched_filepaths = filepaths

	def _match_created_date(filepaths, period):
		for filepath in filepaths:
			file_stat = filepath.stat()

			if platform.system() == 'Windows':
				created_timestamp = file_stat.st_ctime
			else:
				try:
					created_timestamp = file_stat.st_birthtime
				except AttributeError:
					# Settle for modified time on *nix systems
					# not supporting birth time.
					created_timestamp = file_stat.st_mtime

			if pendulum.from_timestamp(created_timestamp) in period:
				yield filepath

	def _match_modified_date(filepaths, period):
		for filepath in filepaths:
			modified_timestamp = filepath.stat().st_mtime

			if pendulum.from_timestamp(modified_timestamp) in period:
				yield filepath

	for period in [
		created_in,
		created_on,
		created_before,
		created_after,
	]:
		if period is not None:
			matched_filepaths = _match_created_date(matched_filepaths, period)

	for period in [
		modified_in,
		modified_on,
		modified_before,
		modified_after,
	]:
		if period is not None:
			matched_filepaths = _match_modified_date(matched_filepaths, period)

	return list(matched_filepaths)


def generate_magnet_link(torrent_info):
	torrent_name = torrent_info['info']['name']
	info_hash = hash_info_dict(torrent_info['info'])
	data_size = calculate_torrent_size(torrent_info)

	magnet_link = f'magnet:?dn={torrent_name}&xt=urn:btih:{info_hash}&xl={data_size}'

	if 'announce-list' in torrent_info:
		for tier in torrent_info['announce-list']:
			magnet_link += f'&tr={random.choice(tier)}'
	elif 'announce' in torrent_info:
		magnet_link += f'&tr={torrent_info["announce"]}'

	return magnet_link


def get_files(
	filepath,
	*,
	max_depth=float('inf'),
	exclude_paths=None,
	exclude_regexes=None,
	exclude_globs=None
):
	"""Create a list of files from given filepath."""

	files = []

	if filepath.is_file():
		files.append(filepath)
	elif filepath.is_dir():
		start_level = len(filepath.parts)

		for path in filepath.glob('**/*'):
			if (
				path.is_file()
				and len(path.parent.parts) - start_level <= max_depth
			):
				files.append(path)

	return files


def output_abbreviations(conf):
	def abbr_list(abbrs):
		lines = []
		for abbr, tracker in abbrs.items():
			if isinstance(tracker, list):
				line = f'{crayons.cyan(abbr)}: ' + '\n'.ljust(23).join(
					crayons.magenta(track)
					for track in tracker
				)
			else:
				line = f'{crayons.cyan(abbr)}: {crayons.magenta(tracker)}'

			lines.append(line)

		return '\n'.ljust(17).join(lines)

	auto_abbrs = abbr_list(
		{
			'open': "All default trackers in a random tiered order.",
			'random': "A single random default tracker.",
		}
	)
	default_abbrs = abbr_list(
		{
			abbr: tracker
			for abbr, tracker in DEFAULT_ABBRS.items()
			if abbr not in ['open', 'random']
		}
	)
	user_abbrs = abbr_list(conf['trackers'])

	summary = (
		f"\n"
		f"{crayons.yellow('Config File')}:    {crayons.cyan(CONFIG_PATH)}\n\n"
		f"{crayons.yellow('Auto')}:           {auto_abbrs}\n\n"
		f"{crayons.yellow('Default')}:        {default_abbrs}\n\n"
		f"{crayons.yellow('User')}:           {user_abbrs}"
	)

	print(summary)


def output_summary(torrent_info, show_files=False):
	torrent_name = torrent_info['info']['name']
	info_hash = hash_info_dict(torrent_info['info'])
	private = 'Yes' if torrent_info['info'].get('private') == 1 else 'No'

	announce_list = None
	if 'announce-list' in torrent_info:
		announce_list = torrent_info['announce-list']
	elif 'announce' in torrent_info:
		announce_list = [[torrent_info['announce']]]

	if announce_list:
		tracker_list = '\n\n'.ljust(18).join(
			'\n'.ljust(17).join(
				tracker
				for tracker in tier
			)
			for tier in announce_list
		)
	else:
		tracker_list = None

	data_size = calculate_torrent_size(torrent_info)
	piece_size = torrent_info['info']['piece length']
	piece_count = math.ceil(data_size / piece_size)

	tz = pendulum.tz.local_timezone()
	creation_date = pendulum.from_timestamp(
		torrent_info['creation date'],
		tz
	).format('YYYY-MM-DD HH:mm:ss Z')
	created_by = torrent_info.get('created by', '')
	comment = torrent_info.get('comment', '')
	source = torrent_info.get('source', '')

	magnet_link = generate_magnet_link(torrent_info)

	summary = (
		f"\n"
		f"{crayons.yellow('Info Hash')}:      {crayons.cyan(info_hash)}\n"
		f"{crayons.yellow('Torrent Name')}:   {crayons.cyan(torrent_name)}\n"
		f"{crayons.yellow('Data Size')}:      {crayons.cyan(humanize_size(data_size, precision=2))}\n"
		f"{crayons.yellow('Piece Size')}:     {crayons.cyan(humanize_size(piece_size))}\n"
		f"{crayons.yellow('Piece Count')}:    {crayons.cyan(piece_count)}\n"
		f"{crayons.yellow('Private')}:        {crayons.cyan(private)}\n"
		f"{crayons.yellow('Creation Date')}:  {crayons.cyan(creation_date)}\n"
		f"{crayons.yellow('Created By')}:     {crayons.cyan(created_by)}\n"
		f"{crayons.yellow('Comment')}:        {crayons.cyan(comment)}\n"
		f"{crayons.yellow('Source')}:         {crayons.cyan(source)}\n"
		f"{crayons.yellow('Trackers')}:       {crayons.cyan(tracker_list)}\n\n"
		f"{crayons.yellow('Magnet')}:         {crayons.cyan(magnet_link)}"
	)

	if show_files:
		file_infos = []
		if 'files' in torrent_info['info']:
			for f in torrent_info['info']['files']:
				file_infos.append(
					(
						humanize_size(f['length'], precision=2),
						Path(*f['path']),
					)
				)
		else:
			file_infos.append(
				(
					humanize_size(
						torrent_info['info']['length'], precision=2
					),
					Path(torrent_info['info']['name']),
				)
			)

		pad = len(
			max(
				(size for size, _ in file_infos),
				key=len
			)
		)

		summary += f"\n\n{crayons.yellow('Files')}:\n\n"
		for size, path in file_infos:
			summary += f"    {crayons.white(f'{size:<{pad}}')}  {crayons.green(path)}\n"

	print(summary)


def read_torrent_file(filepath):
	try:
		torrent_info = bencode.load(filepath.open('rb'))
	except FileNotFoundError:
		raise FileNotFoundError(f"{filepath} not found.")
	except TypeError:
		raise TypeError(f"Could not parse {filepath}.")

	return torrent_info


def write_torrent_file(filepath, torrent_info):
	bencode.dump(torrent_info, filepath.open('wb'))
