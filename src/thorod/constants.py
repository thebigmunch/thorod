import re

CYGPATH_RE = re.compile("^(?:/[^/]+)*/?$")
"""Regex pattern matching UNIX-style filepaths."""

B = 1024 ** 0
KIB = 1024 ** 1
MIB = 1024 ** 2
GIB = 1024 ** 3
TIB = 1024 ** 4

SYMBOLS = [
	(TIB, 'TiB'), (GIB, 'GiB'), (MIB, 'MiB'), (KIB, 'KiB'), (B, 'B')
]

PIECE_SIZE_VALUES = [
	16 * KIB, 32 * KIB, 64 * KIB, 128 * KIB, 256 * KIB, 512 * KIB,
	1 * MIB, 2 * MIB, 4 * MIB, 8 * MIB, 16 * MIB, 32 * MIB
]

PIECE_SIZE_STRINGS = ['16k', '32k', '64k', '128k', '256k', '512k', '1m', '2m', '4m', '8m', '16m', '32m', 'auto']

PIECE_SIZES = dict(zip(PIECE_SIZE_STRINGS, PIECE_SIZE_VALUES))
