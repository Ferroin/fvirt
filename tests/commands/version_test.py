# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.version'''

from __future__ import annotations

import re

from click.testing import CliRunner

from fvirt import VERSION
from fvirt.cli import cli
from fvirt.libvirt import API_VERSION

OUTPUT_REGEX = re.compile('^fvirt ([0-9]+\\.[0-9]+\\.[0-9]+), using libvirt-python ([0-9]+\\.[0-9]+\\.[0-9])$')


def test_version() -> None:
    '''Test that the version command properly reports the version.'''
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0

    matches = OUTPUT_REGEX.match(result.output)

    assert matches

    assert matches.group(1) == str(VERSION)


def test_api_version() -> None:
    '''Test that the version command properly reports the api version.'''
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0

    matches = OUTPUT_REGEX.match(result.output)

    assert matches

    assert matches.group(2) == str(API_VERSION)
