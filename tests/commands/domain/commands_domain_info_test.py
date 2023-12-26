# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain.info'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.domain._mixin import DomainMixin

from ..shared import check_info_output

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click.testing import Result

    from fvirt.libvirt import Hypervisor


def test_command_run(runner: Callable[[Sequence[str], int], Result], test_hv: Hypervisor) -> None:
    '''Test that the command runs correctly.'''
    uri = str(test_hv.uri)

    result = runner(('-c', uri, 'domain', 'info', '1'), 0)
    assert len(result.output) > 0

    dom = test_hv.domains.get(1)
    assert dom is not None

    check_info_output(result.output, dom, 'Domain: 1', DomainMixin)
