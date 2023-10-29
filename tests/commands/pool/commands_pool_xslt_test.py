# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.xslt'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from click.testing import Result

    from fvirt.libvirt import Hypervisor, StoragePool


def test_command_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool: tuple[StoragePool, Hypervisor],
    xslt_doc_factory: Callable[[str, str], str],
    tmp_path: Path,
) -> None:
    '''Test that the command runs correctly.'''
    pool, hv = live_pool
    uri = str(hv.uri)
    target = 'target/path'
    new_value = str(tmp_path)
    xslt_path = tmp_path / 'transform.xslt'

    e = pool.config.find(f'/{target}')
    assert e is not None
    assert e.text != new_value

    xslt_path.write_text(xslt_doc_factory(target, new_value))

    result = runner(('-c', uri, 'pool', 'xslt', str(xslt_path), pool.name), 0)

    assert len(result.output) > 0

    e = pool.config.find(f'/{target}')
    assert e is not None

    assert e.text == new_value


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_pool_group: tuple[tuple[StoragePool, ...], Hypervisor],
    xslt_doc_factory: Callable[[str, str], str],
    tmp_path: Path,
    object_name_prefix: str,
) -> None:
    '''Test running the command on multiple objects.'''
    pools, hv = live_pool_group
    uri = str(hv.uri)
    target = 'target/path'
    new_value = str(tmp_path)
    xslt_path = tmp_path / 'transform.xslt'

    for pool in pools:
        e = pool.config.find(f'/{target}')
        assert e is not None
        assert e.text != new_value

    xslt_path.write_text(xslt_doc_factory(target, new_value))

    result = runner(('-c', uri, 'pool', 'xslt', str(xslt_path), '--match', 'name', object_name_prefix), 0)
    assert len(result.output) > 0

    for pool in pools:
        e = pool.config.find(f'/{target}')
        assert e is not None
        assert e.text == new_value
