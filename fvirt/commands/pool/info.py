# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping info for a pool.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import StoragePoolMixin
from .._base.info import InfoCommand


@final
class _PoolInfo(InfoCommand, StoragePoolMixin):
    pass


info: Final = _PoolInfo(
    name='info',
)

__all__ = [
    'info',
]
