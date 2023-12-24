# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to stop storage pools.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import StoragePoolMixin
from .._base.lifecycle import StopCommand


@final
class _PoolStop(StopCommand, StoragePoolMixin):
    pass


stop: Final = _PoolStop(
    name='stop',
)

__all__ = [
    'stop',
]
