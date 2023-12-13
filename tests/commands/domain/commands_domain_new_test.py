# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.new'''

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


def test_command_run_define(
    runner: Callable[[Sequence[str], int], Result],
    live_hv: Hypervisor,
    live_dom_xml: Callable[[], str],
    tmp_path: Path,
    serial: Callable[[str], _GeneratorContextManager],
) -> None:
    '''Test that the command runs correctly.'''
    uri = str(live_hv.uri)
    xml = live_dom_xml()
    xml_file = tmp_path / 'domain.xml'
    xml_file.write_text(xml)
    e = etree.XML(xml).find('./name')
    assert e is not None
    name = e.text
    assert name is not None

    with serial('live-domain'):
        result = runner(('-c', uri, 'domain', 'new', '--define', str(xml_file)), 0)

    assert len(result.output) > 0

    dom = live_hv.domains.get(name)
    assert dom is not None
    assert not dom.running


def test_command_bulk_run_define(
    runner: Callable[[Sequence[str], int], Result],
    live_hv: Hypervisor,
    live_dom_xml: Callable[[], str],
    tmp_path: Path,
    serial: Callable[[str], _GeneratorContextManager],
) -> None:
    '''Test running the command on multiple objects.'''
    count = 3
    uri = str(live_hv.uri)
    xmls = tuple(
        live_dom_xml() for _ in range(0, count)
    )
    names = []
    paths = []

    for i, x in enumerate(xmls):
        e = etree.XML(x).find('./name')
        assert e is not None
        assert e.text is not None
        names.append(e.text)

        p = tmp_path / f'domain{i}.xml'
        p.write_text(x)
        paths.append(str(p))

    with serial('live-domain'):
        result = runner(('-c', uri, 'domain', 'new', '--define') + tuple(str(p) for p in paths), 0)

    assert len(result.output) > 0

    for name in names:
        dom = live_hv.domains.get(name)

        assert dom is not None
        assert not dom.running


@pytest.mark.xfail(reason='Failing due to an unknown internal error.')
def test_command_run_create(
    runner: Callable[[Sequence[str], int], Result],
    live_hv: Hypervisor,
    live_dom_xml: Callable[[], str],
    tmp_path: Path,
    serial: Callable[[str], _GeneratorContextManager],
) -> None:
    '''Test that the command runs correctly.'''
    uri = str(live_hv.uri)
    xml = live_dom_xml()
    xml_file = tmp_path / 'domain.xml'
    xml_file.write_text(xml)
    e = etree.XML(xml).find('./name')
    assert e is not None
    name = e.text
    assert name is not None

    with serial('live-domain'):
        result = runner(('-c', uri, 'domain', 'new', '--create', str(xml_file)), 0)

    assert len(result.output) > 0

    dom = live_hv.domains.get(name)
    assert dom is not None
    assert dom.running


@pytest.mark.xfail(reason='Failing due to an unknown internal error.')
def test_command_bulk_run_create(
    runner: Callable[[Sequence[str], int], Result],
    live_hv: Hypervisor,
    live_dom_xml: Callable[[], str],
    tmp_path: Path,
    serial: Callable[[str], _GeneratorContextManager],
) -> None:
    '''Test running the command on multiple objects.'''
    count = 3
    uri = str(live_hv.uri)
    xmls = tuple(
        live_dom_xml() for _ in range(0, count)
    )
    names = []
    paths = []

    for i, x in enumerate(xmls):
        e = etree.XML(x).find('./name')
        assert e is not None
        assert e.text is not None
        names.append(e.text)

        p = tmp_path / f'domain{i}.xml'
        p.write_text(x)
        paths.append(str(p))

    with serial('live-domain'):
        result = runner(('-c', uri, 'domain', 'new', '--create') + tuple(str(p) for p in paths), 0)

    assert len(result.output) > 0

    for name in names:
        dom = live_hv.domains.get(name)

        assert dom is not None
        assert dom.running
