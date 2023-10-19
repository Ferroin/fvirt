# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to set the autostart state for one or more storage pools.'''

from __future__ import annotations

from typing import Final, final

from .._base.autostart import AutostartCommand
from .._base.objects import StoragePoolMixin
from ...libvirt.storage_pool import MATCH_ALIASES


@final
class _PoolAutostart(AutostartCommand, StoragePoolMixin):
    pass


autostart: Final = _PoolAutostart(
    name='autostart',
    aliases=MATCH_ALIASES,
)

__all__ = (
    'autostart',
)
