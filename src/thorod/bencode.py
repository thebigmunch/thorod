"""A simple bencoding implementation with standard API."""

from collections.abc import Mapping
from io import SEEK_CUR, BytesIO


def _bytes(data):
	return bytes(str(data), 'utf8')


def _str(data):
	try:
		return data.decode("utf8")
	except UnicodeDecodeError:
		return data


def _read_until(data, end=b'e'):
	buffer = bytearray()
	d = data.read(1)

	while d != end:
		buffer += d
		d = data.read(1)

	return buffer


def _bdecode_dict(data):
	result = {}

	key = _bdecode(data)

	while key:
		result[key] = _bdecode(data)

		key = _bdecode(data)

	return result


def _bdecode_int(data):
	return int(_read_until(data))


def _bdecode_list(data):
	result = []

	item = _bdecode(data)

	while item:
		result.append(item)

		item = _bdecode(data)

	return result


def _bdecode_str(data):
	length = int(_read_until(data, b':'))

	item = data.read(length)

	return _str(item)


def _bdecode(data):
	type_char = data.read(1)

	if type_char == b'i':
		return _bdecode_int(data)
	elif type_char.isdigit():
		data.seek(-1, SEEK_CUR)
		return _bdecode_str(data)
	elif type_char == b'l':
		return _bdecode_list(data)
	elif type_char == b'd':
		return _bdecode_dict(data)


def _bencode(data):
	if isinstance(data, int):
		return _bytes(f'i{data}e')
	elif isinstance(data, str):
		length = len(_bytes(data))
		return _bytes(f'{length}:{data}')
	elif isinstance(data, (bytes, bytearray)):
		return _bytes(len(data)) + b':' + data
	elif isinstance(data, list):
		return b'l' + b''.join(_bencode(d) for d in data) + b'e'
	elif isinstance(data, Mapping):
		enc_dict = bytes()

		for key in sorted(data):
			enc_dict += _bencode(key) + _bencode(data[key])

		return b'd' + enc_dict + b'e'
	else:
		raise TypeError(
			f"{type(data)} is not a valid type for bencoding."
		)


def dump(obj, fp):
	fp.write(_bencode(obj))


def dumps(obj):
	return _bencode(obj)


def load(fp):
	return _bdecode(fp)


def loads(data):
	if isinstance(data, str):
		data = data.encode()

	return _bdecode(BytesIO(data))
