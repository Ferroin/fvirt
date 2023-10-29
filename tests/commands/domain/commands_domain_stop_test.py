# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.stop'''

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Domain, Hypervisor


def test_command_run(
    runner: Callable[[Sequence[str], int], Result],
    test_dom: tuple[Domain, Hypervisor],
) -> None:
    '''Test that the command runs correctly.'''
    dom, hv = test_dom

    assert dom.running

    uri = str(hv.uri)

    result = runner(('-c', uri, 'domain', 'stop', dom.name), 0)
    assert len(result.output) > 0

    assert not dom.running


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    test_dom_group: tuple[tuple[Domain, ...], Hypervisor],
    object_name_prefix: str,
) -> None:
    '''Test running the command on multiple objects.'''
    doms, hv = test_dom_group
    uri = str(hv.uri)

    assert all(d.running for d in doms)

    result = runner(('-c', uri, 'domain', 'stop', '--match', 'name', object_name_prefix), 0)
    assert len(result.output) > 0

    assert all((not d.running) for d in doms)
