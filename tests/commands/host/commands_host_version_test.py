# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.host.version'''

import re

from click.testing import CliRunner

from fvirt.cli import cli

LINE1_REGEX = re.compile('^libvirt: v[0-9]+\\.[0-9]+\\.[0-9]$')
LINE2_REGEX = re.compile('^Hypervisor \\(.+?\\): v[0-9]+\\.[0-9]+\\.[0-9]$')


def test_libvirt_version() -> None:
    '''Test that the host version command reports the libvirt version.'''
    runner = CliRunner()
    result = runner.invoke(cli, ['host', 'version'])
    assert result.exit_code == 0

    lines = result.output.splitlines()
    assert len(lines) == 2
    assert LINE1_REGEX.match(lines[0])


def test_hypervisor_version() -> None:
    '''Test that the host version command reports the hypervisor version.'''
    runner = CliRunner()
    result = runner.invoke(cli, ['-c', 'qemu:///session', 'host', 'version'])
    assert result.exit_code == 0

    lines = result.output.splitlines()
    assert len(lines) == 2
    assert LINE1_REGEX.match(lines[0])
