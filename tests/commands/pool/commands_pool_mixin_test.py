# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.storage_pool._mixin'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.pool._mixin import StoragePoolMixin

from ..shared import check_mixin

if TYPE_CHECKING:
    from fvirt.libvirt import Hypervisor, StoragePool


def storage_pool_mixin_consistency_test(test_pool: tuple[StoragePool, Hypervisor]) -> None:
    '''Check that the structure of StoragePoolMixin is correct.'''
    pool, _ = test_pool

    check_mixin(StoragePoolMixin, pool)
