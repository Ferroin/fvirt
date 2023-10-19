# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to undefine storage pools.'''

from __future__ import annotations

from typing import Final, final

from .._base.lifecycle import UndefineCommand
from .._base.objects import StoragePoolMixin
from ...libvirt.storage_pool import MATCH_ALIASES


@final
class _PoolUndefine(UndefineCommand, StoragePoolMixin):
    pass


undefine: Final = _PoolUndefine(
    name='undefine',
    aliases=MATCH_ALIASES,
)

__all__ = [
    'undefine',
]
