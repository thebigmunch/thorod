# thorod

[![PyPI](https://img.shields.io/pypi/v/thorod.svg?label=PyPI)](https://pypi.org/project/thorod/)
![](https://img.shields.io/badge/Python-3.6%2B-blue.svg)  
[![GitHub CI](https://img.shields.io/github/workflow/status/thebigmunch/thorod/CI?label=GitHub%20CI)](https://github.com/thebigmunch/thorod/actions?query=workflow%3ACI)  
[![Docs - Stable](https://img.shields.io/readthedocs/thorod/stable.svg?label=Docs%20%28Stable%29)](https://thorod.readthedocs.io/en/stable/)
[![Docs - Latest](https://img.shields.io/readthedocs/thorod/latest.svg?label=Docs%20%28Latest%29)](https://thorod.readthedocs.io/en/latest/)

[thorod](https://github.com/thebigmunch/thorod) is a CLI utility for torrent creation and manipulation.

## What's a thorod?

Thorod means torrent (of water) in the Tolkien Elvish language of Sindarin.

## Why use thorod?

There are many CLI torrent utilities out there, so here are some unique or notable features of thorod:

* All torrents are unique; a random salt is added to all created/xseeded torrents.
* Supports trackers on the same tier.
* Type less with tracker abbreviations.
	* Includes a number of open public trackers by default.
	* Includes auto generated open and random abbreviations to help balance load between open public trackers.
	* Users can list/add/remove their own tracker abbreviations directly from CLI as well as manually editing config file.
* Generate magnet links on creation or on command.
* Has an xseed command to generate a cross-seedable torrent without re-hashing files.
* View information about a torrent file in the terminal, rather than adding it to a torrent client.
* Simple automatic piece size calculation from 16 KiB to 32 MiB on by default. Users can set manually by option.
* Supports source key in info dict used by private trackers.


## Installation

``pip install -U thorod``


## Usage

For the release version, see the [stable docs](https://thorod.readthedocs.io/en/stable/).  
For the development version, see the [latest docs](https://thorod.readthedocs.io/en/latest/).


## Appreciation

Showing appreciation is always welcome.

#### Thank

[![Say Thanks](https://img.shields.io/badge/thank-thebigmunch-blue.svg?style=flat-square)](https://saythanks.io/to/thebigmunch)

Get your own thanks inbox at [SayThanks.io](https://saythanks.io/).

#### Contribute

[Contribute](https://github.com/thebigmunch/thorod/blob/master/.github/CONTRIBUTING.md) by submitting bug reports, feature requests, or code.

#### Help Others/Stay Informed

[Discourse forum](https://forum.thebigmunch.me/)

#### Referrals/Donations

[![Digital Ocean](https://img.shields.io/badge/Digital_Ocean-referral-orange.svg?style=flat-square)](https://bit.ly/DigitalOcean-tbm-referral) [![Namecheap](https://img.shields.io/badge/Namecheap-referral-orange.svg?style=flat-square)](http://bit.ly/Namecheap-tbm-referral) [![PayPal](https://img.shields.io/badge/PayPal-donate-brightgreen.svg?style=flat-square)](https://bit.ly/PayPal-thebigmunch)
