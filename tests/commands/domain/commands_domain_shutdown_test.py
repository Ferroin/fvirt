# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.shutdown'''

from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

import pytest

from fvirt.commands._base.exitcode import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Domain, Hypervisor


@pytest.mark.slow
@pytest.mark.parametrize('opts, expected, delay', (
    (
        tuple(),
        0,
        15,
    ),
    (
        ('--timeout', '0'),
        int(ExitCode.OPERATION_FAILED),
        15,
    ),
    (
        ('--timeout', '15'),
        0,
        0,
    ),
    (
        ('--force',),
        int(ExitCode.OPERATION_FAILED),
        0,
    ),
))
def test_command_run(
    opts: tuple[str, ...],
    expected: int,
    delay: int,
    runner: Callable[[Sequence[str], int], Result],
    live_dom: tuple[Domain, Hypervisor],
) -> None:
    '''Test that the command runs correctly.'''
    dom, hv = live_dom
    uri = str(hv.uri)
    iter_delay = 0.2

    dom.start(idempotent=True)

    assert dom.running == True  # noqa: E712
    sleep(3)  # Ensure the domain has finished startup
    assert dom.running == True  # noqa: E712

    result = runner(('-c', uri, 'domain', 'shutdown', dom.name) + opts, expected)
    assert len(result.output) > 0

    t = 0.0
    while t < delay:
        if not dom.running:
            break

        t += iter_delay
        sleep(iter_delay)

    assert dom.running == False  # noqa: E712


def test_command_bulk_run(
    runner: Callable[[Sequence[str], int], Result],
    live_dom_group: tuple[tuple[Domain, ...], Hypervisor],
    object_name_prefix: str,
) -> None:
    '''Test running the command on multiple objects.'''
    doms, hv = live_dom_group
    uri = str(hv.uri)

    for dom in doms:
        dom.start(idempotent=True)

    assert all(dom.running for dom in doms)
    sleep(5)  # Ensure the domains have finished startup
    assert all(dom.running for dom in doms)

    result = runner(('-c', uri, 'domain', 'shutdown', '--match', 'name', object_name_prefix), 0)
    assert len(result.output) > 0

    t = 0.0
    while t < 15:
        if all((not dom.running) for dom in doms):
            break

        t += 0.2
        sleep(0.2)

    assert all((not dom.running) for dom in doms)
