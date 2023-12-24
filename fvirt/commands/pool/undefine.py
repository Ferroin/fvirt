# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to undefine storage pools.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import StoragePoolMixin
from .._base.lifecycle import UndefineCommand


@final
class _PoolUndefine(UndefineCommand, StoragePoolMixin):
    pass


undefine: Final = _PoolUndefine(
    name='undefine',
)

__all__ = [
    'undefine',
]
