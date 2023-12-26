# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.volume._mixin'''

from __future__ import annotations

from typing import TYPE_CHECKING

from fvirt.commands.volume._mixin import VolumeMixin

from ..shared import check_mixin

if TYPE_CHECKING:
    from fvirt.libvirt import Hypervisor, StoragePool, Volume


def volume_mixin_consistency_test(live_volume: tuple[Volume, StoragePool, Hypervisor]) -> None:
    '''Check that the structure of VolumeMixin is correct.'''
    vol, _, _ = live_volume

    check_mixin(VolumeMixin, vol)
