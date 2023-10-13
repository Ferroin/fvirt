# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.host.version'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING

from fvirt.cli import cli

if TYPE_CHECKING:
    from click.testing import CliRunner

LINE1_REGEX = re.compile('^libvirt: v[0-9]+\\.[0-9]+\\.[0-9]$')
LINE2_REGEX = re.compile('^Hypervisor \\(.+?\\): v[0-9]+\\.[0-9]+\\.[0-9]$')


def test_libvirt_version(cli_runner: CliRunner, test_uri: str) -> None:
    '''Test that the host version command reports the libvirt version.'''
    result = cli_runner.invoke(cli, ['-c', test_uri, 'host', 'version'])
    assert result.exit_code == 0

    lines = result.output.splitlines()
    assert len(lines) == 2
    assert LINE1_REGEX.match(lines[0])


def test_hypervisor_version(cli_runner: CliRunner, test_uri: str) -> None:
    '''Test that the host version command reports the hypervisor version.'''
    result = cli_runner.invoke(cli, ['-c', test_uri, 'host', 'version'])
    assert result.exit_code == 0

    lines = result.output.splitlines()
    assert len(lines) == 2
    assert LINE1_REGEX.match(lines[0])
