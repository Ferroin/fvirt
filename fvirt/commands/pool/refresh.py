# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to refresh storage pools.'''

from __future__ import annotations

from typing import Final, Self, final

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from .._base.objects import StoragePoolMixin


@final
class _RefreshCommand(SimpleLifecycleCommand, StoragePoolMixin):
    '''Class for refreshing storage pools.'''
    @property
    def METHOD(self: Self) -> str: return 'refresh'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='refresh',
            continuous='refreshing',
            past='refreshed',
            idempotent_state='',
        )


refresh: Final = _RefreshCommand(
    name='refresh',
)

__all__ = [
    'refresh',
]
