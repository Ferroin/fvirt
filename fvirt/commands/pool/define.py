# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to define a new storage pool.'''

from __future__ import annotations

from typing import Final, final

from .._base.new import DefineCommand
from .._base.objects import StoragePoolMixin


@final
class _PoolDefine(DefineCommand, StoragePoolMixin):
    pass


define: Final = _PoolDefine(
    name='define',
)

__all__ = [
    'define',
]
