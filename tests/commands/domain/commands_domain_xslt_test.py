# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.xslt'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from click.testing import Result

    from fvirt.libvirt import Domain, Hypervisor


def test_command_run(
    runner: Callable[[Sequence[str], int], Result],
    test_dom: tuple[Domain, Hypervisor],
    xslt_doc_factory: Callable[[str, str], str],
    tmp_path: Path,
) -> None:
    '''Test that the command runs correctly.'''
    dom, hv = test_dom
    uri = str(hv.uri)
    target = 'on_crash'
    new_value = 'restart'
    xslt_path = tmp_path / 'transform.xslt'

    e = dom.config.find(f'/{target}')
    assert e is not None
    assert e.text != new_value

    xslt_path.write_text(xslt_doc_factory(target, new_value))

    result = runner(('-c', uri, 'domain', 'xslt', str(xslt_path), dom.name), 0)
    assert len(result.output) > 0

    e = dom.config.find(target)
    assert e is not None

    assert e.text == new_value


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    test_dom_group: tuple[tuple[Domain, ...], Hypervisor],
    xslt_doc_factory: Callable[[str, str], str],
    tmp_path: Path,
    object_name_prefix: str,
) -> None:
    '''Test running the command on multiple objects.'''
    doms, hv = test_dom_group
    uri = str(hv.uri)
    target = 'on_crash'
    new_value = 'restart'
    xslt_path = tmp_path / 'transform.xslt'

    for dom in doms:
        e = dom.config.find(f'/{target}')
        assert e is not None
        assert e.text != new_value

    xslt_path.write_text(xslt_doc_factory(target, new_value))

    result = runner(('-c', uri, 'domain', 'xslt', str(xslt_path), '--match', 'name', object_name_prefix), 0)
    assert len(result.output) > 0

    for dom in doms:
        e = dom.config.find(f'/{target}')
        assert e is not None
        assert e.text == new_value
