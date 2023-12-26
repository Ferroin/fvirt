# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.domain._mixin'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.domain._mixin import DomainMixin

from ..shared import check_mixin

if TYPE_CHECKING:
    from fvirt.libvirt import Domain, Hypervisor


def domain_mixin_consistency_test(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that the structure of DomainMixin is correct.'''
    dom, _ = test_dom

    check_mixin(DomainMixin, dom)
