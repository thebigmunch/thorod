import sys

import pendulum
from sortedcontainers import SortedDict
from tbm_utils import (
	filter_filepaths_by_dates,
	get_filepaths,
)

from .config import (
	read_config_file,
	write_config_file,
)
from .core import (
	create_dir_info_dict,
	create_file_info_dict,
	read_torrent_file,
	write_torrent_file,
)
from .output import (
	generate_abbreviations_outputs,
	generate_magnet_link,
	generate_magnet_outputs,
	generate_summary_outputs,
	render,
)
from .utils import (
	calculate_data_size,
	calculate_piece_size,
	generate_unique_string,
)


def do_abbrs(args):
	conf = read_config_file()

	if args._subcommand == 'add':
		conf['trackers'][args.abbreviation] = args.tracker
	elif args._subcommand in ['rem', 'remove']:
		for abbreviation in args.abbreviations:
			try:
				del conf['trackers'][abbreviation]
			except KeyError:
				pass

	write_config_file(conf)
	outputs = generate_abbreviations_outputs(conf)
	render(outputs)


def do_create(args):
	torrent_info = SortedDict()

	filepaths = get_filepaths(
		args.input,
		max_depth=args.max_depth,
		exclude_paths=args.exclude_paths,
		exclude_regexes=args.exclude_regexes,
		exclude_globs=args.exclude_globs
	)

	creation_dates = [
		args[option]
		for option in [
			'created_in',
			'created_on',
			'created_before',
			'created_after',
		]
		if option in args
	]

	modification_dates = [
		args[option]
		for option in [
			'modified_in',
			'modified_on',
			'modified_before',
			'modified_after',
		]
		if option in args
	]

	filepaths = filter_filepaths_by_dates(
		filepaths,
		creation_dates=creation_dates,
		modification_dates=modification_dates,
	)

	filepaths = list(filepaths)

	if not filepaths:
		sys.exit("\nNo files matching criteria found.")

	data_size = calculate_data_size(filepaths)
	piece_size = calculate_piece_size(data_size, threshold=args.piece_threshold)

	if not args.trackers:
		private = False
	else:
		private = args.private

	if args.input.is_dir():
		info_dict = create_dir_info_dict(
			args.input,
			filepaths,
			data_size,
			piece_size,
			private,
			args.source,
			args.md5,
			show_progress=args.show_progress,
		)
	elif args.input.is_file():
		info_dict = create_file_info_dict(
			filepaths,
			data_size,
			piece_size,
			private,
			args.source,
			args.md5,
			show_progress=args.show_progress,
		)

	torrent_info['info'] = info_dict

	if args.trackers:
		torrent_info['announce'] = args.trackers[0][0]

		if len(args.trackers) > 1 or len(args.trackers[0]) > 1:
			torrent_info['announce-list'] = args.trackers

	if args.created_by is not None:
		torrent_info['created by'] = args.created_by

	if args.comment is not None:
		torrent_info['comment'] = args.comment

	torrent_info['creation date'] = pendulum.now('utc').int_timestamp

	torrent_info['encoding'] = 'UTF-8'

	write_torrent_file(args.output, torrent_info)

	outputs = generate_summary_outputs(torrent_info, show_files=args.show_files)
	render(outputs)


def do_info(args):
	torrent_info = read_torrent_file(args.torrent)

	outputs = generate_summary_outputs(torrent_info, show_files=args.show_files)
	render(outputs)


def do_magnet(args):
	torrent_info = read_torrent_file(args.torrent)
	magnet_link = generate_magnet_link(torrent_info)

	outputs = generate_magnet_outputs(magnet_link)
	render(outputs)


def do_xseed(args):
	torrent_info = read_torrent_file(args.torrent)

	if (
		not isinstance(torrent_info, dict)
		or 'info' not in torrent_info
	):
		raise ValueError(
			f"{args.torrent} is not a valid torrent file."
		)

	for k in ['announce-list', 'comment']:
		torrent_info.pop(k, None)

	torrent_info['info']['salt'] = generate_unique_string()

	if not args.trackers:
		torrent_info['info']['private'] = 0
	elif args.private is not None:
		torrent_info['info']['private'] = 1 if args.private else 0

	torrent_info['info'].pop('source', None)
	if args.source is not None:
		torrent_info['info']['source'] = args.source

	if args.trackers:
		torrent_info['announce'] = args.trackers[0][0]

		if len(args.trackers) > 1 or len(args.trackers[0]) > 1:
			torrent_info['announce-list'] = args.trackers
	else:
		torrent_info.pop('announce', None)
		torrent_info.pop('announce-list', None)

	if args.created_by is not None:
		torrent_info['created by'] = args.created_by

	if args.comment is not None:
		torrent_info['comment'] = args.comment

	torrent_info['creation date'] = pendulum.now('utc').int_timestamp

	torrent_info['encoding'] = 'UTF-8'

	write_torrent_file(args.output, torrent_info)

	outputs = generate_summary_outputs(torrent_info)
	render(outputs)
