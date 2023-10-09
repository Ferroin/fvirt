# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.cli'''

from click.testing import CliRunner

from fvirt.cli import cli


def test_bare_invoke() -> None:
    '''Test that we actually run at all.'''
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code != 0


def test_load_check() -> None:
    '''Test that lazy loading doesn’t run into any major issues.'''
    runner = CliRunner()
    result = runner.invoke(cli, ['help'])
    assert result.exit_code == 0
