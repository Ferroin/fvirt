# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to delete storage pools.'''

from __future__ import annotations

from typing import Final, Self, final

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from .._base.objects import StoragePoolMixin


@final
class _DeleteCommand(SimpleLifecycleCommand, StoragePoolMixin):
    '''A class for deleting a storage pool.'''
    @property
    def METHOD(self: Self) -> str: return 'delete'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='delete',
            continuous='deleting',
            past='deleted',
            idempotent_state='undefined',
        )


delete: Final = _DeleteCommand(
    name='delete',
)

__all__ = [
    'delete',
]
