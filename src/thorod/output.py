import math
import random
from pathlib import PurePath

import pendulum
from rich.bar import Bar
from rich.console import Console
from rich.progress import (
	BarColumn,
	Progress,
	ProgressColumn,
)
from rich.table import Table
from rich.text import Text
from tbm_utils import (
	cast_to_list,
	humanize_duration,
	humanize_filesize,
)

from .config import CONFIG_PATH
from .constants import DEFAULT_ABBRS
from .utils import (
	calculate_torrent_size,
	hash_info_dict,
)


CONSOLE = Console()


class BarColumn(BarColumn):
	def render(self, task):
		return Bar(
			total=task.total,
			completed=task.completed,
			width=self.bar_width,
			style='dim white',
		)


class ElapsedColumn(ProgressColumn):
	def render(self, task):
		elapsed = task.elapsed
		if elapsed is None:
			return Text("00:00", style="bold cyan")
		return Text(f" {humanize_duration(elapsed)}", style="bold cyan")


class ETAColumn(ProgressColumn):
	# Only refresh twice a second to prevent jitter
	max_refresh = 0.5

	def render(self, task):
		remaining = task.time_remaining
		if remaining is None:
			return Text("?", style="bold cyan")
		return Text(f"({humanize_duration(remaining)})", style="bold cyan")


class HashingSpeedColumn(ProgressColumn):
	max_refresh = 0.5

	def render(self, task):
		speed = task.speed
		if speed is None:
			return Text("?", style="bold red")
		hashing_speed = humanize_filesize(speed)
		return Text(f"{hashing_speed}/s", style="bold red")


PROGRESS = Progress(
	' ',
	'[bold magenta]{task.percentage:>3.0f}%',
	BarColumn(bar_width=60),
	HashingSpeedColumn(),
	'•',
	ElapsedColumn(),
	ETAColumn(),
	refresh_per_second=5,
)


def generate_abbreviations_outputs(conf):
	outputs = ['\n']

	config_table = Table(
		box=None,
		show_footer=False,
		show_edge=False,
		header_style="bold yellow underline",
	)
	config_table.add_column(
		'File',
		style='cyan',
	)
	config_table.add_row(None)
	config_table.add_row(str(CONFIG_PATH))

	outputs.append(config_table)

	auto_abbrs_table = Table(
		box=None,
		show_footer=False,
		show_edge=False,
		header_style="bold yellow underline",
	)

	auto_abbrs_table.add_column(
		'Auto',
		style='yellow',
	)
	auto_abbrs_table.add_column(style='cyan')

	auto_abbrs_table.add_row(None)
	auto_abbrs_table.add_row(
		'open',
		'All default trackers in a random tiered order.',
	)
	auto_abbrs_table.add_row(
		'random',
		'A single random default tracker.',
	)

	outputs.extend(['\n', auto_abbrs_table])

	default_abbrs_table = Table(
		box=None,
		show_footer=False,
		show_edge=False,
		header_style="bold yellow underline",
	)

	default_abbrs_table.add_column(
		'Default',
		style='yellow',
	)
	default_abbrs_table.add_column(style='cyan')

	default_abbrs_table.add_row(None)
	for abbr, tracker in DEFAULT_ABBRS.items():
		default_abbrs_table.add_row(abbr, tracker)

	outputs.extend(['\n', default_abbrs_table])

	user_abbrs = conf.get('trackers')
	if user_abbrs:
		user_abbrs_table = Table(
			box=None,
			show_footer=False,
			show_edge=False,
			header_style="bold yellow underline",
		)

		user_abbrs_table.add_column(
			'User',
			style='yellow',
		)
		user_abbrs_table.add_column(style='cyan')

		user_abbrs_table.add_row(None)
		for abbr, tracker in user_abbrs.items():
			user_abbrs_table.add_row(abbr, tracker)

		outputs.extend(['\n', user_abbrs_table])

	return outputs


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


def generate_magnet_outputs(magnet_link):
	outputs = ['\n']

	magnet_table = Table(
		box=None,
		show_footer=False,
		show_edge=False,
		header_style="bold yellow underline",
	)

	magnet_table.add_column(
		'Magnet',
		style='cyan',
	)

	magnet_table.add_row(None)
	magnet_table.add_row(magnet_link)

	outputs.append(magnet_table)

	return outputs


def generate_summary_outputs(torrent_info, show_files=False):
	outputs = ['\n']

	torrent_name = torrent_info['info']['name']
	info_hash = hash_info_dict(torrent_info['info'])
	private = 'Yes' if torrent_info['info'].get('private') == 1 else 'No'

	announce_list = None
	if 'announce-list' in torrent_info:
		announce_list = torrent_info['announce-list']
	elif 'announce' in torrent_info:
		announce_list = [[torrent_info['announce']]]

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

	summary_table = Table(
		box=None,
		show_footer=False,
		show_edge=False,
		header_style="bold yellow underline",
	)

	summary_table.add_column(
		'Summary',
		style='yellow',
		no_wrap=True,
	)
	summary_table.add_column(style='cyan')

	summary_table.add_row(None)
	summary_table.add_row('Info Hash:', info_hash)
	summary_table.add_row('Torrent Name:', torrent_name)
	summary_table.add_row('Data Size:', humanize_filesize(data_size, precision=2))
	summary_table.add_row('Piece Size:', humanize_filesize(piece_size))
	summary_table.add_row('Piece Count:', str(piece_count))
	summary_table.add_row('Private:', str(private))
	summary_table.add_row('Creation Date:', str(creation_date))
	summary_table.add_row('Created By:', created_by)
	summary_table.add_row('Comment:', comment)
	summary_table.add_row('Source:', source)
	summary_table.add_row('Magnet:', magnet_link)

	outputs.append(summary_table)

	tracker_table = Table(
		box=None,
		show_footer=False,
		show_edge=False,
		header_style="bold yellow underline",
	)
	tracker_table.add_column(
		'Trackers',
		style='yellow',
		no_wrap=True,
	)
	tracker_table.add_column(style='cyan')
	tracker_table.add_row(None)

	if not announce_list:
		tracker_table.add_row('[cyan]None')
	else:
		pad = len(str(len(announce_list)))
		for i, tier in enumerate(announce_list):
			tracker_table.add_row(f"Tier {i:>{pad}}:", '\n'.join(tracker for tracker in tier))

	outputs.extend(['\n', tracker_table])

	if show_files:
		file_infos = []
		if 'files' in torrent_info['info']:
			for f in torrent_info['info']['files']:
				file_infos.append(
					(
						humanize_filesize(f['length'], precision=2),
						PurePath(*f['path']),
					)
				)
		else:
			file_infos.append(
				(
					humanize_filesize(
						torrent_info['info']['length'], precision=2
					),
					PurePath(torrent_info['info']['name']),
				)
			)

		num_pad = len(
			max(
				(
					size.split()[0]
					for size, _ in file_infos
				),
				key=len,
			)
		)
		unit_pad = len(
			max(
				(
					size.split()[1]
					for size, _ in file_infos
				),
				key=len,
			)
		)

		files_table = Table(
			box=None,
			show_footer=False,
			show_edge=False,
			header_style="bold yellow underline",
		)
		files_table.add_column(
			'Files',
			style='yellow',
			no_wrap=True,
		)
		files_table.add_column(style='cyan')
		files_table.add_row(None)

		for size, path in file_infos:
			num, unit = size.split()
			files_table.add_row(f"{num:>{num_pad}} {unit:>{unit_pad}}", str(path))

		outputs.extend(['\n', files_table])

	return outputs


@cast_to_list
def render(outputs, **kwargs):
	for output in outputs:
		CONSOLE.print(output, **kwargs)
