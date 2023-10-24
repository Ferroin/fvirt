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

    from fvirt.libvirt import Volume


def test_column_definitions(test_volume: Volume) -> None:
    '''Test that column definitions are valid.'''
    check_columns(COLUMNS, test_volume)


def test_default_columns() -> None:
    '''Test that the default column list is valid.'''
    check_default_columns(COLUMNS, DEFAULT_COLS)


@pytest.mark.libvirtd
def test_list(runner: Callable[[Sequence[str], int], Result], live_volume: Volume) -> None:
    '''Test the list command.'''
    uri = str(live_volume._hv.uri)
    pool = live_volume._parent
    assert pool is not None

    result = runner(('-c', uri, '--units', 'bytes', 'volume', 'list', pool.name), 0)
    assert result.exit_code == 0

    check_list_output(result.output, live_volume, tuple(COLUMNS[x] for x in DEFAULT_COLS))


@pytest.mark.libvirtd
def test_no_headings(runner: Callable[[Sequence[str], int], Result], live_volume: Volume) -> None:
    '''Test the --no-headings option.'''
    uri = str(live_volume._hv.uri)
    pool = live_volume._parent
    assert pool is not None

    result = runner(('-c', uri, '--units', 'bytes', 'volume', 'list', '--no-headings', pool.name), 0)
    assert result.exit_code == 0

    check_list_entry(result.output, live_volume, tuple(COLUMNS[x] for x in DEFAULT_COLS))


@pytest.mark.libvirtd
def test_list_only_name(runner: Callable[[Sequence[str], int], Result], live_volume: Volume) -> None:
    '''Test listing only names.'''
    uri = str(live_volume._hv.uri)
    pool = live_volume._parent
    assert pool is not None

    result = runner(('-c', uri, 'volume', 'list', '--only', 'name', pool.name), 0)

    assert result.output.rstrip() == str(live_volume.name)


@pytest.mark.libvirtd
def test_list_only_key(runner: Callable[[Sequence[str], int], Result], live_volume: Volume) -> None:
    '''Test listing only keys.'''
    uri = str(live_volume._hv.uri)
    pool = live_volume._parent
    assert pool is not None

    result = runner(('-c', uri, 'volume', 'list', '--only', 'key', pool.name), 0)

    assert result.output.rstrip() == str(live_volume.key)
