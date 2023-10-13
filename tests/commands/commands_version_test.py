# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.version'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING

from fvirt import VERSION
from fvirt.cli import cli
from fvirt.libvirt import API_VERSION

if TYPE_CHECKING:
    from click.testing import CliRunner

OUTPUT_REGEX = re.compile('^fvirt ([0-9]+\\.[0-9]+\\.[0-9]+), using libvirt-python ([0-9]+\\.[0-9]+\\.[0-9])$')


def test_version(cli_runner: CliRunner) -> None:
    '''Test that the version command properly reports the version.'''
    result = cli_runner.invoke(cli, ['version'])
    assert result.exit_code == 0

    matches = OUTPUT_REGEX.match(result.output)

    assert matches

    assert matches.group(1) == str(VERSION)


def test_api_version(cli_runner: CliRunner) -> None:
    '''Test that the version command properly reports the api version.'''
    result = cli_runner.invoke(cli, ['version'])
    assert result.exit_code == 0

    matches = OUTPUT_REGEX.match(result.output)

    assert matches

    assert matches.group(2) == str(API_VERSION)
