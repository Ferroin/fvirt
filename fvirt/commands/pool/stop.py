# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to stop storage pools.'''

from __future__ import annotations

from typing import Final, final

from .._base.lifecycle import StopCommand
from .._base.objects import StoragePoolMixin
from ...libvirt.storage_pool import MATCH_ALIASES


@final
class _PoolStop(StopCommand, StoragePoolMixin):
    pass


stop: Final = _PoolStop(
    name='stop',
    aliases=MATCH_ALIASES,
)

__all__ = [
    'stop',
]
