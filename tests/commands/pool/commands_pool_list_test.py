# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.list'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fvirt.cli import cli
from fvirt.commands.pool.list import COLUMNS, DEFAULT_COLS

from ..shared import check_columns, check_default_columns, check_list_entry, check_list_output

if TYPE_CHECKING:
    from click.testing import CliRunner

    from fvirt.libvirt import StoragePool


def test_column_definitions(test_pool: StoragePool) -> None:
    '''Test that column definitions are valid.'''
    check_columns(COLUMNS, test_pool)


def test_default_columns() -> None:
    '''Test that the default column list is valid.'''
    check_default_columns(COLUMNS, DEFAULT_COLS)


@pytest.mark.libvirtd
def test_list(cli_runner: CliRunner, test_pool: StoragePool) -> None:
    '''Test the list command.'''
    uri = str(test_pool._hv.uri)

    result = cli_runner.invoke(cli, ('-c', uri, '--units', 'bytes', 'pool', 'list', '--match', 'name', test_pool.name))
    assert result.exit_code == 0

    check_list_output(result.output, test_pool, tuple(COLUMNS[x] for x in DEFAULT_COLS))


@pytest.mark.libvirtd
def test_no_headings(cli_runner: CliRunner, test_pool: StoragePool) -> None:
    '''Test the --no-headings option.'''
    uri = str(test_pool._hv.uri)

    result = cli_runner.invoke(cli, ('-c', uri, '--units', 'bytes', 'pool', 'list', '--no-headings', '--match', 'name', test_pool.name))
    assert result.exit_code == 0

    check_list_entry(result.output, test_pool, tuple(COLUMNS[x] for x in DEFAULT_COLS))


@pytest.mark.libvirtd
def test_list_only_name(cli_runner: CliRunner, test_pool: StoragePool) -> None:
    '''Test listing only names.'''
    uri = str(test_pool._hv.uri)

    result = cli_runner.invoke(cli, ('-c', uri, 'pool', 'list', '--only', 'name', '--match', 'name', test_pool.name))
    assert result.exit_code == 0

    assert result.output.rstrip() == str(test_pool.name)


@pytest.mark.libvirtd
def test_list_only_uuid(cli_runner: CliRunner, test_pool: StoragePool) -> None:
    '''Test listing only UUIDs.'''
    uri = str(test_pool._hv.uri)

    result = cli_runner.invoke(cli, ('-c', uri, 'pool', 'list', '--only', 'uuid', '--match', 'name', test_pool.name))
    assert result.exit_code == 0

    assert result.output.rstrip() == str(test_pool.uuid)
