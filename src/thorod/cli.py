import argparse
import math
from pathlib import Path

import colorama
from tbm_utils import (
	Namespace,
	SubcommandHelpFormatter,
	UsageHelpFormatter,
	create_parser_filter_dates,
	create_parser_local,
	create_parser_meta,
	custom_path,
	datetime_string_to_time_period,
	get_defaults,
	merge_defaults,
	parse_args
)

from . import __title__, __version__
from .commands import (
	do_abbrs,
	do_create,
	do_info,
	do_magnet,
	do_xseed,
)
from .config import ABBRS, read_config_file
from .constants import (
	DEFAULT_ABBRS,
	DEFAULT_TRACKERS,
	PIECE_SIZE_STRINGS,
)

COMMAND_KEYS = {
	'abbrs',
	'create',
	'info',
	'magnet',
	'xseed',
}

colorama.init()


#########
# Utils #
#########

def is_usable_abbr(value):
	if value in DEFAULT_ABBRS:
		raise argparse.ArgumentTypeError(
			f"'{value}' is a default abbreviation. Please choose another."
		)

	return value


def replace_abbreviations(value):
	announce_list = []

	def process_trackers(trackers):
		random_trackers = DEFAULT_TRACKERS.copy()

		tier_list = []
		for item in trackers:
			if isinstance(item, list):
				process_trackers(item)
			elif item == 'open':
				for tracker in DEFAULT_TRACKERS:
					announce_list.append([tracker])
			elif item == 'random':

				tier_list.append(random_trackers.pop())
			else:
				tier_list.append(ABBRS.get(item, item))

		if tier_list:
			announce_list.append(tier_list)

	process_trackers([tier.split('^') for tier in value])

	return announce_list


########
# Meta #
########

meta = create_parser_meta(__title__, __version__)


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

local = create_parser_local()


##########
# Filter #
##########

filter_dates = create_parser_filter_dates()


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
	'--piece-threshold',
	metavar='TRESHOLD',
	type=int,
	help=(
		"Set piece count threshold for automatic piece size calculation.\n"
		"Defaults to 2000."
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
		"Trackers on the same tier are separated with a carat (^)\n\n"
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
	defaults.piece_threshold = 2000
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

	config_defaults = get_defaults(
		args._command,
		read_config_file(),
		command_keys=COMMAND_KEYS
	)

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
				defaults[k] = datetime_string_to_time_period(v, in_=True)
			elif k.endswith('on'):
				defaults[k] = datetime_string_to_time_period(v, on=True)
			elif k.endswith('before'):
				defaults[k] = datetime_string_to_time_period(v, before=True)
			elif k.endswith('after'):
				defaults[k] = datetime_string_to_time_period(v, after=True)
		else:
			defaults[k] = v

	return defaults


def run():
	try:
		parsed = parse_args(thorod)

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
