# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.list'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.pool._mixin import StoragePoolMixin

from ..shared import check_list_entry, check_list_output

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_list(runner: Callable[[Sequence[str], int], Result], test_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test the list command.'''
    pool, hv = test_pool
    uri = str(hv.uri)

    result = runner(('-c', uri, '--units', 'bytes', 'pool', 'list', '--match', 'name', pool.name), 0)

    check_list_output(result.output, pool, StoragePoolMixin)


def test_no_headings(runner: Callable[[Sequence[str], int], Result], test_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test the --no-headings option.'''
    pool, hv = test_pool
    uri = str(hv.uri)

    result = runner(('-c', uri, '--units', 'bytes', 'pool', 'list', '--no-headings', '--match', 'name', pool.name), 0)

    check_list_entry(result.output, pool, StoragePoolMixin)


def test_list_only_name(runner: Callable[[Sequence[str], int], Result], test_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test listing only names.'''
    pool, hv = test_pool
    uri = str(hv.uri)

    result = runner(('-c', uri, 'pool', 'list', '--only', 'name', '--match', 'name', pool.name), 0)

    assert result.output.rstrip() == str(pool.name)


def test_list_only_uuid(runner: Callable[[Sequence[str], int], Result], test_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Test listing only UUIDs.'''
    pool, hv = test_pool
    uri = str(hv.uri)

    result = runner(('-c', uri, 'pool', 'list', '--only', 'uuid', '--match', 'name', pool.name), 0)

    assert result.output.rstrip() == str(pool.uuid)
