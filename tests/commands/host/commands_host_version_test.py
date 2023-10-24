# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Core tests for fvirt.commands.host.version'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

LINE1_REGEX = re.compile('^libvirt: v[0-9]+\\.[0-9]+\\.[0-9]$')
LINE2_REGEX = re.compile('^Hypervisor \\(.+?\\): v[0-9]+\\.[0-9]+\\.[0-9]$')


def test_libvirt_version(runner: Callable[[Sequence[str], int], Result], test_uri: str) -> None:
    '''Test that the host version command reports the libvirt version.'''
    result = runner(('-c', test_uri, 'host', 'version'), 0)

    lines = result.output.splitlines()
    assert len(lines) == 2
    assert LINE1_REGEX.match(lines[0])


def test_hypervisor_version(runner: Callable[[Sequence[str], int], Result], test_uri: str) -> None:
    '''Test that the host version command reports the hypervisor version.'''
    result = runner(('-c', test_uri, 'host', 'version'), 0)

    lines = result.output.splitlines()
    assert len(lines) == 2
    assert LINE1_REGEX.match(lines[0])
