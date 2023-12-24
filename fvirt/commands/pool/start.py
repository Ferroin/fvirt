# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start storage pools.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import StoragePoolMixin
from .._base.lifecycle import StartCommand


@final
class _PoolStart(StartCommand, StoragePoolMixin):
    pass


start: Final = _PoolStart(
    name='start',
)

__all__ = [
    'start',
]
