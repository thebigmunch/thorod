# Change Log

Notable changes to this project based on the [Keep a Changelog](https://keepachangelog.com) format.
This project adheres to [Semantic Versioning](https://semver.org).


## [Unreleased](https://github.com/thebigmunch/thorod/tree/master)

[Commits](https://github.com/thebigmunch/thorod/compare/1.1.0...master)

### Added

* Trackerless torrent support.
* Ability to set defaults in config file.
* Options to exclude filepaths by:
	* strings
	* regexes
	* globs
* Options to filter files by:
	* creation date/time
	* modification date/time

### Changed

* Use argparse instead of click for CLI.
* Update default trackers.
* ``torrent`` command to ``create``.
* thorod no longer defaults to ``create``.

### Fixed

* Torrent file naming when input path is a directory.


## [1.1.0](https://github.com/thebigmunch/thorod/releases/tag/1.1.0) (2018-09-27)

[Commits](https://github.com/thebigmunch/thorod/compare/1.0.0...1.1.0)

### Changed

* Change abbrs list output format.
* Colorize output.


## [1.0.0](https://github.com/thebigmunch/thorod/releases/tag/1.0.0) (2018-09-26)

[Commits](https://github.com/thebigmunch/thorod/commit/5707eb6abccba83552c544c427e403b03c603514)

* Initial release.
