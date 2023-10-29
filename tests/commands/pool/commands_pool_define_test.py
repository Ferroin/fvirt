# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.pool.define'''

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from lxml import etree

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import _GeneratorContextManager
    from pathlib import Path

    from click.testing import Result

    from fvirt.libvirt import Hypervisor


def test_command_run(
    runner: Callable[[Sequence[str], int], Result],
    live_hv: Hypervisor,
    pool_xml: Callable[[], str],
    tmp_path: Path,
    serial: Callable[[str], _GeneratorContextManager],
) -> None:
    '''Test that the command runs correctly.'''
    uri = str(live_hv.uri)
    conf_path = tmp_path / 'pool.xml'
    xml = pool_xml()
    conf_path.write_text(xml)
    e = etree.XML(xml).find('./name')
    assert e is not None
    name = e.text
    assert name is not None

    with serial('live-pool'):
        result = runner(('-c', uri, 'pool', 'define', str(conf_path)), 0)

    assert len(result.output) > 0

    pool = live_hv.storage_pools.get(name)

    assert pool is not None
    assert not pool.running


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_hv: Hypervisor,
    pool_xml: Callable[[], str],
    tmp_path: Path,
    serial: Callable[[str], _GeneratorContextManager],
) -> None:
    '''Test running the command on multiple objects.'''
    uri = str(live_hv.uri)
    count = 3
    xmls = tuple(
        pool_xml() for _ in range(0, count)
    )
    names = []
    paths = []

    for i, x in enumerate(xmls):
        e = etree.XML(x).find('./name')
        assert e is not None
        assert e.text is not None
        names.append(e.text)

        p = tmp_path / f'pool{i}.xml'
        p.write_text(x)
        paths.append(str(p))

    with serial('live-pool'):
        result = runner(('-c', uri, 'pool', 'define') + tuple(paths), 0)

    assert len(result.output) > 0

    for name in names:
        pool = live_hv.storage_pools.get(name)

        assert pool is not None
        assert not pool.running
