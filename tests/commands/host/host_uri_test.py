# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.host.uri'''

from click.testing import CliRunner

from fvirt.cli import cli


def test_uri() -> None:
    '''Test that the host uri command properly reports the URI.'''
    runner = CliRunner()
    result = runner.invoke(cli, ['-c', 'test:///default', 'host', 'uri'])
    assert result.exit_code == 0
    assert result.output == 'test:///default\n'
