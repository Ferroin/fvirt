# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.volume.list'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fvirt.commands.volume.list import COLUMNS, DEFAULT_COLS

from ..shared import check_columns, check_default_columns, check_list_entry, check_list_output

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool, Volume


def test_column_definitions(test_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test that column definitions are valid.'''
    vol, _, _ = test_volume
    check_columns(COLUMNS, vol)


def test_default_columns() -> None:
    '''Test that the default column list is valid.'''
    check_default_columns(COLUMNS, DEFAULT_COLS)


def test_list(runner: Callable[[Sequence[str], int], Result], live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test the list command.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)

    result = runner(('-c', uri, '--units', 'bytes', 'volume', 'list', pool.name), 0)
    assert result.exit_code == 0

    check_list_output(result.output, vol, tuple(COLUMNS[x] for x in DEFAULT_COLS))


def test_no_headings(runner: Callable[[Sequence[str], int], Result], live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test the --no-headings option.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)

    result = runner(('-c', uri, '--units', 'bytes', 'volume', 'list', '--no-headings', pool.name), 0)
    assert result.exit_code == 0

    check_list_entry(result.output, vol, tuple(COLUMNS[x] for x in DEFAULT_COLS))


def test_list_only_name(runner: Callable[[Sequence[str], int], Result], live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test listing only names.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)

    result = runner(('-c', uri, 'volume', 'list', '--only', 'name', pool.name), 0)

    assert result.output.rstrip() == str(vol.name)


def test_list_only_key(runner: Callable[[Sequence[str], int], Result], live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Test listing only keys.'''
    vol, pool, hv = live_volume
    uri = str(hv.uri)

    result = runner(('-c', uri, 'volume', 'list', '--only', 'key', pool.name), 0)

    assert result.output.rstrip() == str(vol.key)
