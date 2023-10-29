# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.autostart'''

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
    uri = str(hv.uri)

    assert dom.autostart == False  # noqa: E712

    result = runner(('-c', uri, 'domain', 'autostart', '--enable', dom.name), 0)
    assert len(result.output) > 0

    assert dom.autostart == True  # noqa: E712

    result = runner(('-c', uri, 'domain', 'autostart', '--disable', dom.name), 0)
    assert len(result.output) > 0

    assert dom.autostart == False  # noqa: E712


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    test_dom_group: tuple[tuple[Domain, ...], Hypervisor],
    object_name_prefix: str,
) -> None:
    '''Test running the command on multiple objects.'''
    doms, hv = test_dom_group
    uri = str(hv.uri)

    assert all((not p.autostart) for p in doms)

    result = runner(('-c', uri, 'domain', 'autostart', '--enable', '--match', 'name', object_name_prefix), 0)
    assert len(result.output) > 0

    assert all(p.autostart for p in doms)
