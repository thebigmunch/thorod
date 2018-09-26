#!/usr/bin/env python3

import os

from setuptools import find_packages, setup

base_dir = os.path.dirname(__file__)

about = {}
with open(os.path.join(base_dir, 'src', 'thorod', '__about__.py')) as f:
	exec(f.read(), about)

setup(
	name=about['__title__'],
	version=about['__version__'],
	description=about['__summary__'],
	url=about['__url__'],
	license=about['__license__'],
	author=about['__author__'],
	author_email=about['__author_email__'],

	keywords=[],
	classifiers=[
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
	],

	install_requires=[
		'appdirs>=1.4',
		'click>=6.0',
		'click-default-group>=1.2',
		'pendulum>=2.0',
		'sphinx-click>=1.0',
		'toml>=0.9.4',
		'tqdm>=4.19',
	],

	packages=find_packages('src'),
	package_dir={
		'': 'src'
	},

	entry_points={
		'console_scripts': [
			'thorod = thorod.cli:thorod'
		]
	}
)
