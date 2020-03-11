from hashlib import md5, sha1

from sortedcontainers import SortedDict

from . import bencode
from .output import (
	PROGRESS,
	render,
)
from .utils import (
	generate_unique_string,
	get_file_path,
)


def create_dir_info_dict(
	base_path,
	filepaths,
	data_size,
	piece_size,
	private,
	source,
	include_md5,
	*,
	show_progress=True,
):
	def hash_files(progress=None, task=None):
		data = bytes()
		file_infos = []
		pieces = bytearray()

		for filepath in filepaths:
			file_dict = SortedDict()
			length = 0

			md5sum = md5() if include_md5 else None

			with open(filepath, 'rb') as f:
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

					if progress:
						progress.update(
							task,
							advance=len(piece),
						)

			file_dict['length'] = length
			file_dict['path'] = get_file_path(filepath, base_path)

			if include_md5:
				file_dict['md5sum'] = md5sum.hexdigest()

			file_infos.append(file_dict)

		if len(data) > 0:
			pieces += sha1(data).digest()

		return file_infos, pieces

	if show_progress:
		render("\n Hashing Files\n\n", style="bold yellow")

		with PROGRESS:
			task = PROGRESS.add_task(
				"Hashing",
				total=data_size,
			)
			file_infos, pieces = hash_files(PROGRESS, task)
	else:
		file_infos, pieces = hash_files()

	info_dict = SortedDict()
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
	filepaths,
	data_size,
	piece_size,
	private,
	source,
	include_md5,
	show_progress=True,
):
	def hash_file(progress=None, task=None):
		pieces = bytearray()
		length = 0
		md5sum = md5() if include_md5 else None

		with open(filepaths[0], 'rb') as f:
			while True:
				piece = f.read(piece_size)

				if not piece:
					break

				length += len(piece)

				pieces += sha1(piece).digest()

				if include_md5:
					md5sum.update(piece)

				if progress:
					progress.update(
						task,
						advance=len(piece),
					)

		return pieces, length, md5sum

	if show_progress:
		render("\n Hashing Files\n\n", style="bold yellow")

		with PROGRESS:
			task = PROGRESS.add_task(
				"Hashing",
				total=data_size,
			)

			pieces, length, md5sum = hash_file(PROGRESS, task)
	else:
		pieces, length, md5sum = hash_file()

	info_dict = SortedDict()
	info_dict['name'] = filepaths[0].name
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
