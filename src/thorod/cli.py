import argparse
import math
import os
import re
from pathlib import Path

import pendulum
from attr import attrib, attrs
from pendulum import DateTime
from pendulum.tz import fixed_timezone

from . import __title__, __version__
from .commands import (
	do_abbrs,
	do_create,
	do_info,
	do_magnet,
	do_xseed,
)
from .config import (
	ABBRS,
	get_defaults,
)
from .constants import (
	DEFAULT_ABBRS,
	PIECE_SIZE_STRINGS,
	UNIX_PATH_RE,
)
from .utils import (
	DictMixin,
	convert_unix_path,
)


DATETIME_RE = re.compile(
	r"(?P<year>\d{4})"
	r"[-\s]?"
	r"(?P<month>\d{1,2})?"
	r"[-\s]?"
	r"(?P<day>\d{1,2})?"
	r"[T\s]?"
	r"(?P<hour>\d{1,2})?"
	r"[:\s]?"
	r"(?P<minute>\d{1,2})?"
	r"[:\s]?"
	r"(?P<second>\d{1,2})?"
	r"(?P<tz_oper>[+\-\s])?"
	r"(?P<tz_hour>\d{1,2})?"
	r"[:\s]?"
	r"(?P<tz_minute>\d{1,2})?"
)


def _convert_to_int(value):
	if value is not None:
		value = int(value)

	return value


@attrs(slots=True, frozen=True, kw_only=True)
class ParsedDateTime:
	year = attrib(converter=_convert_to_int)
	month = attrib(converter=_convert_to_int)
	day = attrib(converter=_convert_to_int)
	hour = attrib(converter=_convert_to_int)
	minute = attrib(converter=_convert_to_int)
	second = attrib(converter=_convert_to_int)
	tz_oper = attrib()
	tz_hour = attrib(converter=_convert_to_int)
	tz_minute = attrib(converter=_convert_to_int)


class Namespace(DictMixin):
	pass


class UsageHelpFormatter(argparse.RawTextHelpFormatter):
	def add_usage(self, usage, actions, groups, prefix="Usage: "):
		super().add_usage(usage, actions, groups, prefix)


# Removes the command list while leaving the usage metavar intact.
class SubcommandHelpFormatter(UsageHelpFormatter):
	def _format_action(self, action):
		parts = super()._format_action(action)
		if action.nargs == argparse.PARSER:
			parts = "\n".join(parts.split("\n")[1:])
		return parts


#########
# Utils #
#########

# I use Windows Python install from Cygwin.
# This custom click type converts Unix-style paths to Windows-style paths in this case.
def custom_path(value):
	if os.name == 'nt' and UNIX_PATH_RE.match(str(value)):
		value = Path(convert_unix_path(str(value)))

	value = Path(value)

	return value


def is_usable_abbr(value):
	if value in DEFAULT_ABBRS:
		raise argparse.ArgumentTypeError(
			f"'{value}' is a default abbreviation. Please choose another."
		)

	return value


def replace_abbreviations(value):
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


def time_period(
	dt_string,
	*,
	in_=False,
	on=False,
	before=False,
	after=False
):
	if dt_string == 'today':
		dt_string = pendulum.today().to_date_string()
	elif dt_string == 'yesterday':
		dt_string = pendulum.yesterday().to_date_string()

	match = DATETIME_RE.match(dt_string)

	if not match or match['year'] is None:
		raise argparse.ArgumentTypeError(
			f"'{dt_string}' is not a supported datetime string."
		)

	parsed = ParsedDateTime(**match.groupdict())

	if parsed.tz_hour:
		tz_offset = 0
		if parsed.tz_hour is not None:
			tz_offset += parsed.tz_hour * 3600
		if parsed.tz_minute is not None:
			tz_offset += parsed.tz_minute * 60
		if parsed.tz_oper == '-':
			tz_offset *= -1
		parsed_tz = fixed_timezone(tz_offset)
	else:
		parsed_tz = pendulum.local_timezone()

	if in_:
		if parsed.day:
			raise argparse.ArgumentTypeError(
				f"Datetime string must contain only year or year/month for 'in' option."
			)
		start = pendulum.datetime(
			parsed.year,
			parsed.month or 1,
			parsed.day or 1,
			tz=parsed_tz
		)

		if parsed.month:
			end = start.end_of('month')
		else:
			end = start.end_of('year')

		return pendulum.period(start, end)
	elif on:
		if (
			not all(
				getattr(parsed, attr)
				for attr in ['year', 'month', 'day']
			)
			or parsed.hour
		):
			raise argparse.ArgumentTypeError(
				f"Datetime string must contain only year, month, and day for 'on' option."
			)

		dt = pendulum.datetime(
			parsed.year,
			parsed.month,
			parsed.day,
			tz=parsed_tz
		)

		return pendulum.period(dt.start_of('day'), dt.end_of('day'))
	elif before:
		start = DateTime.min

		dt = pendulum.datetime(
			parsed.year,
			parsed.month or 1,
			parsed.day or 1,
			parsed.hour or 23,
			parsed.minute or 59,
			parsed.second or 59,
			0,
			tz=parsed_tz
		)

		if not parsed.month:
			dt = dt.start_of('year')
		elif not parsed.day:
			dt = dt.start_of('month')
		elif not parsed.hour:
			dt = dt.start_of('day')
		elif not parsed.minute:
			dt = dt.start_of('hour')
		elif not parsed.second:
			dt = dt.start_of('minute')

		return pendulum.period(start, dt)
	elif after:
		end = DateTime.max

		dt = pendulum.datetime(
			parsed.year,
			parsed.month or 1,
			parsed.day or 1,
			parsed.hour or 23,
			parsed.minute or 59,
			parsed.second or 59,
			99999,
			tz=parsed_tz
		)

		if not parsed.month:
			dt = dt.end_of('year')
		elif not parsed.day:
			dt = dt.end_of('month')
		elif not parsed.hour:
			dt = dt.start_of('day')
		elif not parsed.minute:
			dt = dt.start_of('hour')
		elif not parsed.second:
			dt = dt.start_of('minute')

		return pendulum.period(dt, end)


########
# Meta #
########

meta = argparse.ArgumentParser(
	add_help=False
)

meta_options = meta.add_argument_group("Options")
meta_options.add_argument(
	'-h', '--help',
	action='help',
	help="Display help."
)
meta_options.add_argument(
	'-V', '--version',
	action='version',
	version=f"{__title__} {__version__}",
	help="Output version."
)


########
# Show #
########

# Files

show_files = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

show_files_options = show_files.add_argument_group("Show")
show_files_options.add_argument(
	'--show-files',
	action='store_true',
	help="Show files in the summary."
)
show_files_options.add_argument(
	'--hide-files',
	action='store_true',
	help="Don't show files in the summary."
)

# Progress

show_progress = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False,
)

show_progress_options = show_progress.add_argument_group("Show")
show_progress_options.add_argument(
	'--show-progress',
	action='store_true',
	help="Show hashing progress bar."
)
show_progress_options.add_argument(
	'--hide-progress',
	action='store_true',
	help="Hide hashing progress bar."
)


#########
# Local #
#########

local = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

local_options = local.add_argument_group("Local")
local_options.add_argument(
	'--no-recursion',
	action='store_true',
	help=(
		"Disable recursion when scanning for local files.\n"
		"Recursion is enabled by default."
	)
)
local_options.add_argument(
	'--max-depth',
	metavar='DEPTH',
	type=int,
	help=(
		"Set maximum depth of recursion when scanning for local files.\n"
		"Default is infinite recursion."
	)
)
local_options.add_argument(
	'-xp', '--exclude-path',
	metavar='PATH',
	action='append',
	dest='exclude_paths',
	help=(
		"Exclude filepaths.\n"
		"Can be specified multiple times."
	)
)
local_options.add_argument(
	'-xr', '--exclude-regex',
	metavar='RX',
	action='append',
	dest='exclude_regexes',
	help=(
		"Exclude filepaths using regular expressions.\n"
		"Can be specified multiple times."
	)
)
local_options.add_argument(
	'-xg', '--exclude-glob',
	metavar='GP',
	action='append',
	dest='exclude_globs',
	help=(
		"Exclude filepaths using glob patterns.\n"
		"Can be specified multiple times.\n"
		"Absolute glob patterns not supported."
	)
)


##########
# Filter #
##########

filter_dates = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

dates_options = filter_dates.add_argument_group("Filter")
dates_options.add_argument(
	'--created-in',
	metavar='DATE',
	type=lambda d: time_period(d, in_=True),
	help="Include files created in year or year/month."
)
dates_options.add_argument(
	'--created-on',
	metavar='DATE',
	type=lambda d: time_period(d, on=True),
	help="Include files created on date."
)
dates_options.add_argument(
	'--created-before',
	metavar='DATE',
	type=lambda d: time_period(d, before=True),
	help="Include files created before datetime."
)
dates_options.add_argument(
	'--created-after',
	metavar='DATE',
	type=lambda d: time_period(d, after=True),
	help="Include files created after datetime."
)
dates_options.add_argument(
	'--modified-in',
	metavar='DATE',
	type=lambda d: time_period(d, in_=True),
	help="Include files created in year or year/month."
)
dates_options.add_argument(
	'--modified-on',
	metavar='DATE',
	type=lambda d: time_period(d, on=True),
	help="Include files created on date."
)
dates_options.add_argument(
	'--modified-before',
	metavar='DATE',
	type=lambda d: time_period(d, before=True),
	help="Include files modified before datetime."
)
dates_options.add_argument(
	'--modified-after',
	metavar='DATE',
	type=lambda d: time_period(d, after=True),
	help="Include files modified after datetime."
)


###########
# Torrent #
###########

torrent = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)
torrent_options = torrent.add_argument_group("Torrent")
torrent_options.add_argument(
	'--piece-size',
	metavar='SIZE',
	help=(
		"Set piece size.\n"
		"Defaults to automatic calculation.\n"
		f"({', '.join(PIECE_SIZE_STRINGS)})"
	)
)
torrent_options.add_argument(
	'--created-by',
	metavar='CREATOR',
	help=(
		"Set created by field.\n"
		f"Defaults to '{__title__} {__version__}'."
	)
)
torrent_options.add_argument(
	'-c', '--comment',
	metavar='COMMENT',
	help="Set comment field."
)
torrent_options.add_argument(
	'-p', '--private',
	action='store_true',
	help="Make torrent private."
)
torrent_options.add_argument(
	'-P', '--public',
	action='store_true',
	help="Make torrent public."
)
torrent_options.add_argument(
	'-s', '--source',
	metavar='SOURCE',
	help="Set source field."
)
torrent_options.add_argument(
	'--md5',
	action='store_true',
	help="Add md5 hash to info dict."
)


##########
# Output #
##########

output = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

output_options = output.add_argument_group("Output")
output_options.add_argument(
	'-o', '--output',
	metavar='NAME',
	type=lambda p: custom_path(p),
	help=(
		"Set name of torrent file.\n"
		"Defaults to input file or directory name."
	)
)


#########
# Input #
#########

input_ = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

input_options = input_.add_argument_group("Input")
input_options.add_argument(
	'input',
	metavar='PATH',
	type=lambda p: custom_path(p).resolve(),
	help="File or directory."
)

torrent_input = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

torrent_input_options = torrent_input.add_argument_group("Input")
torrent_input_options.add_argument(
	'torrent',
	metavar='TORRENT',
	type=lambda p: custom_path(p).resolve(),
	help="Torrent file."
)


############
# Trackers #
############

trackers = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

trackers_options = trackers.add_argument_group("Trackers")
trackers_options.add_argument(
	'trackers',
	metavar='TRACKERS',
	nargs='*',
	help=(
		"Tracker tiers are separated by a space.\n"
		"Trackers on the same tier should be quoted and separated with a carat (^)\n\n"
		"Example: 'tracker1^tracker2' tracker3"
	)
)


##########
# thorod #
##########


thorod = argparse.ArgumentParser(
	prog='thorod',
	description="Collection of torrent utilities.",
	usage=argparse.SUPPRESS,
	parents=[meta],
	formatter_class=SubcommandHelpFormatter,
	add_help=False
)

subcommands = thorod.add_subparsers(
	title="Commands",
	dest='_command',
	metavar="<command>"
)


#########
# ABBRS #
#########

abbrs_command = subcommands.add_parser(
	'abbrs',
	description="List/Add/Remove tracker abbreviations.",
	help="List/Add/Remove tracker abbreviations.",
	usage=argparse.SUPPRESS,
	parents=[
		meta
	],
	formatter_class=SubcommandHelpFormatter,
	add_help=False
)
abbrs_command.set_defaults(func=do_abbrs)

abbrs_subcommands = abbrs_command.add_subparsers(
	title="Commands",
	dest='_subcommand',
	metavar="<subcommand>"
)

abbrs_list_command = abbrs_subcommands.add_parser(
	'list',
	description="List tracker abbreviations.",
	help="List tracker abbreviations.",
	usage=argparse.SUPPRESS,
	parents=[
		meta
	],
	formatter_class=UsageHelpFormatter,
	add_help=False
)

abbrs_add_command = abbrs_subcommands.add_parser(
	'add',
	description="Add tracker abbreviations.",
	help="Add tracker abbreviations.",
	usage="thorod abbrs add [ABBREVIATION] [TRACKER]",
	parents=[
		meta
	],
	formatter_class=UsageHelpFormatter,
	add_help=False
)
abbrs_add_command.add_argument(
	'abbreviation',
	metavar='ABBREVIATION',
	help="Abbreviation to use for tracker."
)
abbrs_add_command.add_argument(
	'tracker',
	metavar='TRACKER',
	help="Tracker to abbreviate."
)

abbrs_remove_command = abbrs_subcommands.add_parser(
	'remove',
	description="Remove tracker abbreviations.",
	help="Remove tracker abbreviations.",
	usage="thorod abbrs remove [ABBREVIATIONS]...",
	parents=[
		meta
	],
	formatter_class=UsageHelpFormatter,
	add_help=False
)
abbrs_remove_command.add_argument(
	'abbreviations',
	metavar='ABBREVIATIONS',
	nargs='*',
	help="Abbreviations to remove."
)


##########
# Create #
##########

create_command = subcommands.add_parser(
	'create',
	description="Create a torrent file.",
	help="Create a torrent file.",
	formatter_class=UsageHelpFormatter,
	usage="thorod create [OPTIONS] [PATH] [TRACKERS]...",
	parents=[
		meta,
		show_progress,
		show_files,
		local,
		filter_dates,
		torrent,
		output,
		input_,
		trackers
	],
	add_help=False
)
create_command.set_defaults(func=do_create)


########
# Info #
########

info_command = subcommands.add_parser(
	'info',
	description="Output information about a torrent file.",
	help="Output information about a torrent file.",
	formatter_class=UsageHelpFormatter,
	usage="thorod info [OPTIONS] [TORRENT]",
	parents=[
		meta,
		show_files,
		torrent_input
	],
	add_help=False
)
info_command.set_defaults(func=do_info)


##########
# Magnet #
##########

magnet_command = subcommands.add_parser(
	'magnet',
	description="Generate a magnet link from a torrent file.",
	help="Generate a magnet link from a torrent file.",
	formatter_class=UsageHelpFormatter,
	usage="thorod magnet [OPTIONS] [TORRENT]",
	parents=[
		meta,
		torrent_input
	],
	add_help=False
)
magnet_command.set_defaults(func=do_magnet)


#########
# xseed #
#########

xseed_command = subcommands.add_parser(
	'xseed',
	description="Copy a torrent for cross-seeding.",
	help="Copy a torrent for cross-seeding.",
	formatter_class=UsageHelpFormatter,
	usage="thorod xseed [OPTIONS] [TORRENT]",
	parents=[
		meta,
		torrent,
		output,
		torrent_input,
		trackers
	],
	add_help=False
)
xseed_command.set_defaults(func=do_xseed)


def parse_args(args=None):
	return thorod.parse_args(args=args, namespace=Namespace())


def check_args(args):
	if all(
		option in args
		for option in ['private', 'public']
	):
		raise ValueError("Use one of --private/--public', not both.")

	if all(
		option in args
		for option in ['show_progress', 'hide_progress']
	):
		raise ValueError("Use one of --show-progress/--hide-progress', not both.")

	if all(
		option in args
		for option in ['show_files', 'hide_files']
	):
		raise ValueError("Use one of --show-files/--hide-files', not both.")

	if (
		'torrent' in args
		and not args.torrent.exists()
	):
		raise ValueError(f"'{args.torrent}' does not exist.")

	if (
		'input' in args
		and not args.input.exists()
	):
		raise ValueError(f"'{args.input}' does not exist.")

	if 'trackers' not in args:
		args.trackers = []
	else:
		args.trackers = replace_abbreviations(args.trackers)


def default_args(args):
	defaults = Namespace()

	if 'hide_progress' in args:
		defaults.show_progress = False
		defaults.hide_progress = True
	else:
		defaults.show_progress = True
		defaults.hide_progress = False

	if 'show_files' in args:
		defaults.show_files = True
		defaults.hide_files = False
	else:
		defaults.show_files = False
		defaults.hide_files = True

	defaults.no_recursion = False
	defaults.max_depth = math.inf
	defaults.exclude_paths = []
	defaults.exclude_regexes = []
	defaults.exclude_globs = []

	if 'private' in args:
		defaults.private = True
		defaults.public = False
	else:
		defaults.private = False
		defaults.public = True

	defaults.piece_size = 'auto'
	defaults.created_by = f"{__title__} {__version__}"
	defaults.comment = None
	defaults.source = None
	defaults.md5 = False

	if 'input' in args:
		defaults.output = Path(args.input.name + '.torrent').resolve()
	elif 'torrent' in args:
		defaults.output = args.torrent.with_name(
			str(args.torrent.name).replace('.torrent', '') + '-xseed.torrent'
		)

	config_defaults = get_defaults(args._command)
	for k, v in config_defaults.items():
		if k == 'max_depth':
			defaults.max_depth = int(v)
		elif k == 'private':
			defaults['private'] = True
			defaults['public'] = False
		elif k == 'public':
			defaults['public'] = True
			defaults['public'] = False
		elif k in [
			'show_progress',
			'show_files'
		]:
			defaults[k] = v
			defaults[k.replace('show', 'hide')] = not v
		elif k in [
			'hide_progress',
			'hide_files'
		]:
			defaults[k] = v
			defaults[k.replace('hide', 'show')] = not v
		elif k.startswith(('created', 'modified')):
			if k.endswith('in'):
				defaults[k] = time_period(v, in_=True)
			elif k.endswith('on'):
				defaults[k] = time_period(v, on=True)
			elif k.endswith('before'):
				defaults[k] = time_period(v, before=True)
			elif k.endswith('after'):
				defaults[k] = time_period(v, after=True)
		else:
			defaults[k] = v

	return defaults


def merge_defaults(defaults, parsed):
	args = Namespace()

	args.update(defaults)
	args.update(parsed)

	return args


def run():
	try:
		parsed = parse_args()

		if parsed._command is None:
			thorod.parse_args(['-h'])
		elif parsed._command == 'abbrs':
			parsed.func(parsed)
		else:
			check_args(parsed)
			defaults = default_args(parsed)
			args = merge_defaults(defaults, parsed)

			if args.get('no_recursion'):
				args.max_depth = 0

			args.func(args)
	except KeyboardInterrupt:
		thorod.exit(130, "\nInterrupted by user")
