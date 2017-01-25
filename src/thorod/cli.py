"""Command line interface of thorod."""

import math
import os

import click
import pendulum
from click_default_group import DefaultGroup

from . import __title__, __version__
from .config import ABBRS, CONFIG_FILE, DEFAULT_ABBRS, get_config, write_config_file
from .constants import CYGPATH_RE, PIECE_SIZES, PIECE_SIZE_STRINGS
from .core import (
	create_dir_info_dict, create_file_info_dict, generate_magnet_link,
	read_torrent_file, write_torrent_file
)
from .utils import (
	calculate_data_size, calculate_piece_size, calculate_torrent_size,
	convert_cygwin_path, generate_unique_string, get_files, hash_info_dict, humanize_size
)


# I use Windows Python install from Cygwin or other Unix-like environments on Windows.
# This custom click type converts Unix-style paths to Windows-style paths in these cases.
class CustomPath(click.Path):
	def convert(self, value, param, ctx):
		if os.name == 'nt' and CYGPATH_RE.match(value):
			value = convert_cygwin_path(value)

		return super().convert(value, param, ctx)


def is_torrent_file(ctx, param, value):
	if not value.endswith('.torrent'):
		click.confirm(
			f"Is '{value}' a torrent file?",
			abort=True
		)

	return value


def is_usable_abbr(ctx, param, value):
	if value in DEFAULT_ABBRS:
		raise click.BadParameter(
			f"'{value}' is a default abbreviation. Please choose another.", ctx=ctx, param=param
		)

	return value


def output_abbreviations(conf):
	def abbr_list(abbrs):
		lines = []
		for abbr, tracker in abbrs.items():
			if isinstance(tracker, list):
				line = f'{abbr}: ' + '\n'.ljust(23).join(track for track in tracker)
			else:
				line = f'{abbr}: {tracker}'

			lines.append(line)

		return '\n'.ljust(17).join(lines)

	default_abbrs = abbr_list(DEFAULT_ABBRS)
	user_abbrs = abbr_list(conf['trackers'])

	summary = (
		f"Config File:    {CONFIG_FILE}\n\n"
		f"Default:        {default_abbrs}\n\n"
		f"User:           {user_abbrs}"
	)

	click.echo(summary)


def output_summary(torrent_info, torrent_file, show_files=False):
	info_hash = hash_info_dict(torrent_info['info'])
	private = 'Yes' if torrent_info['info'].get('private') == 1 else 'No'

	if 'announce-list' in torrent_info:
		announce_list = torrent_info['announce-list']
	else:
		announce_list = [[torrent_info['announce']]]

	tracker_list = '\n\n'.ljust(18).join('\n'.ljust(17).join(tracker for tracker in tier) for tier in announce_list)

	data_size = calculate_torrent_size(torrent_info)
	piece_size = torrent_info['info']['piece length']
	piece_count = math.ceil(data_size / piece_size)

	tz = pendulum.tz.local_timezone()
	creation_date = pendulum.from_timestamp(torrent_info['creation date'], tz).format('YYYY-MM-DD HH:mm:ss Z')
	created_by = torrent_info.get('created by', '')
	comment = torrent_info.get('comment', '')
	source = torrent_info.get('source', '')

	magnet_link = generate_magnet_link(torrent_info, torrent_file)

	summary = (
		f'\n'
		f'Info Hash:      {info_hash}\n'
		f'Torrent Name:   {torrent_file}\n'
		f'Data Size:      {humanize_size(data_size, precision=2)}\n'
		f'Piece Size:     {humanize_size(piece_size)}\n'
		f'Piece Count:    {piece_count}\n'
		f'Private:        {private}\n'
		f'Creation Date:  {creation_date}\n'
		f'Created By:     {created_by}\n'
		f'Comment:        {comment}\n'
		f'Source:         {source}\n'
		f'Trackers:       {tracker_list}\n\n'

		f'Magnet:         {magnet_link}'
	)

	if show_files:
		file_infos = []
		if 'files' in torrent_info['info']:
			for f in torrent_info['info']['files']:
				file_infos.append((humanize_size(f['length'], precision=2), os.path.join(*f['path'])))
		else:
			file_infos.append((humanize_size(torrent_info['info']['length'], precision=2), torrent_info['info']['name']))

		pad = len(max([size for size, _ in file_infos], key=len))

		summary += f'\n\nFiles:\n\n'
		for size, path in file_infos:
			summary += f'    {size:<{pad}} -- {path}\n'

	click.echo(summary)


def replace_abbreviations(ctx, param, value):
	announce_list = []

	def process_trackers(trackers):
		tier_list = []

		for item in trackers:
			if isinstance(item, list):
				process_trackers(item)
			elif item == 'open':
				for tracker in ABBRS['open']:
					announce_list.append([tracker])
			else:
				tier_list.append(ABBRS.get(item, item))

		if tier_list:
			announce_list.append(tier_list)

	process_trackers([tier.split('^') for tier in value])

	return announce_list


CONTEXT_SETTINGS = dict(max_content_width=100, help_option_names=['-h', '--help'])


@click.group(cls=DefaultGroup, default='torrent', context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
def thorod():
	"""Collection of torrent creation utilities."""

	pass


@thorod.command()
@click.option('--show-files', is_flag=True, default=False, help="Show list of files in the torrent.")
@click.argument('torrent_file', type=CustomPath(exists=True), callback=is_torrent_file)
def info(show_files, torrent_file):
	"""Output information about a torrent file."""

	torrent_info = read_torrent_file(torrent_file)

	output_summary(torrent_info, torrent_file, show_files=show_files)


@thorod.command()
@click.argument('torrent_file', type=CustomPath(exists=True), callback=is_torrent_file)
def magnet(torrent_file):
	"""Generate a magnet link from a torrent file."""

	torrent_info = read_torrent_file(torrent_file)

	magnet_link = generate_magnet_link(torrent_info, torrent_file)

	output = f"\nMagnet:         {magnet_link}"

	click.echo(output)


@thorod.command()
@click.option(
	'--created-by', metavar='CREATOR', default=f'{__title__} {__version__}',
	help=f"Set created by field.\nDefaults to {__title__} {__version__}."
)
@click.option('-c', '--comment', metavar='COMMENT', help="Set comment field.")
@click.option('-s', '--source', metavar='SOURCE', help="Set source field.")
@click.option('-p/-P', '--private/--public', is_flag=True, default=False, help="Set private flag.")
@click.option(
	'--piece-size', metavar='SIZE', default='auto', type=click.Choice(PIECE_SIZE_STRINGS),
	help=f"Set piece size. Defaults to 'auto'.\n({', '.join(PIECE_SIZE_STRINGS)})"
)
@click.option(
	'-o', '--output', metavar='NAME',
	help="Set name of torrent file.\nDefaults to input file or directory name."
)
@click.option('--md5', is_flag=True, default=False, help="")
@click.option(
	'--max-depth', metavar='DEPTH', type=int,
	help="Set maximum depth of recursion when scanning for files.\nDefault is infinite recursion."
)
@click.option('--show-files', is_flag=True, default=False, help="Show list of files in the summary.")
@click.option('--show-progress/--hide-progress', is_flag=True, default=True, help="Show/hide hashing progress bar.")
@click.argument('input-path', type=CustomPath(exists=True), required=True)
@click.argument('trackers', nargs=-1, callback=replace_abbreviations, required=True)
def torrent(
	created_by, comment, source, private, piece_size, output, md5, max_depth,
	show_files, show_progress, input_path, trackers):
	"""Create a torrent file.

	Tracker tiers are separated by a space.
	Trackers on the same tier should be quoted and separated with a carat (^)

	Example: 'tracker1^tracker2' tracker3
	"""

	if max_depth is None:
		max_depth = float('inf')

	files = list(get_files(input_path, max_depth))
	data_size = calculate_data_size(files)

	if piece_size == 'auto':
		piece_size = calculate_piece_size(data_size)
	else:
		piece_size = PIECE_SIZES[piece_size]

	torrent_info = {}

	if os.path.isdir(input_path):
		info_dict = create_dir_info_dict(files, data_size, piece_size, private, source, md5, show_progress=show_progress)
	elif os.path.isfile(input_path):
		info_dict = create_file_info_dict(files, data_size, piece_size, private, source, md5, show_progress=show_progress)

	torrent_info['info'] = info_dict

	torrent_info['announce'] = trackers[0][0]

	if len(trackers) > 1 or len(trackers[0]) > 1:
		torrent_info['announce-list'] = trackers

	if created_by:
		torrent_info['created by'] = created_by

	if comment:
		torrent_info['comment'] = comment

	torrent_info['creation date'] = pendulum.now('utc').int_timestamp

	torrent_info['encoding'] = 'UTF-8'

	if output:
		torrent_file = output
	else:
		torrent_file = os.path.basename(os.path.abspath(input_path))

	torrent_file += '.torrent'

	write_torrent_file(torrent_file, torrent_info)

	output_summary(torrent_info, torrent_file, show_files=show_files)


@thorod.command()
@click.option(
	'--created-by', metavar='CREATOR', default=f'{__title__} {__version__}',
	help=f"Set created by field.\nDefaults to {__title__} {__version__}."
)
@click.option('-c', '--comment', metavar='COMMENT', help="Set comment field.")
@click.option('-s', '--source', metavar='SOURCE', help="Set source field.")
@click.option('-p/-P', '--private/--public', is_flag=True, default=None, help="Set private flag.")
@click.option(
	'-o', '--output', metavar='NAME',
	help="Set name of torrent file.\nDefaults to input file or directory name."
)
@click.argument('torrent_file', type=CustomPath(exists=True), callback=is_torrent_file, required=True)
@click.argument('trackers', nargs=-1, callback=replace_abbreviations, required=True)
def xseed(created_by, comment, source, private, output, torrent_file, trackers):
	"""Copy a torrent for cross-seeding.

	Tracker tiers are separated by a space.
	Trackers on the same tier should be quoted and separated with a carat (^)

	Example: 'tracker1^tracker2' tracker3
	"""

	torrent_info = read_torrent_file(torrent_file)

	if not isinstance(torrent_info, dict) or 'info' not in torrent_info:
		raise ValueError(f"{torrent_file} is not a valid torrent file.")

	torrent_info['info'].pop('source', None)

	for k in ['announce-list', 'comment']:
		torrent_info.pop(k, None)

	torrent_info['info']['salt'] = generate_unique_string()

	if private is not None:
		torrent_info['info']['private'] = 1 if private else 0

	if source:
		torrent_info['info']['source'] = source

	torrent_info['announce'] = trackers[0][0]

	if len(trackers) > 1 or len(trackers[0]) > 1:
		torrent_info['announce-list'] = trackers

	if created_by:
		torrent_info['created by'] = created_by

	if comment:
		torrent_info['comment'] = comment

	torrent_info['creation date'] = pendulum.now('utc').int_timestamp

	torrent_info['encoding'] = 'UTF-8'

	if output:
		xseed_torrent = output + '.torrent'
	else:
		xseed_torrent = os.path.basename(torrent_file).replace('.torrent', '-xseed.torrent')

	write_torrent_file(xseed_torrent, torrent_info)

	output_summary(torrent_info, torrent_file)


@thorod.group(cls=DefaultGroup, default='list', default_if_no_args=True)
def abbrs():
	"""List/Add/Remove tracker abbreviations."""

	pass


@abbrs.command('list')
def list_abbreviations():
	"""List tracker abbreviations."""

	conf = get_config()

	output_abbreviations(conf)


@abbrs.command('add')
@click.argument('abbreviation', callback=is_usable_abbr, required=True)
@click.argument('tracker', required=True)
def add_abbreviation(abbreviation, tracker):
	"""Add tracker abbreviation."""

	conf = get_config()

	conf['trackers'][abbreviation] = tracker

	write_config_file(conf)

	output_abbreviations(conf)


@abbrs.command('rem')
@click.argument('abbreviations', nargs=-1)
def remove_abbreviations(abbreviations):
	"""Remove tracker abbreviations."""

	conf = get_config()

	for abbreviation in abbreviations:
		conf['trackers'].pop(abbreviation, None)

	write_config_file(conf)

	output_abbreviations(conf)
