# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to delete storage pools.'''

from __future__ import annotations

from typing import Self

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from ...libvirt.storage_pool import MATCH_ALIASES


class _DeleteCommand(SimpleLifecycleCommand):
    '''A class for deleting a libvirt object.

       This class takes care of the callback and operation info for
       a LifecycleCommand.'''
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


delete = _DeleteCommand(
    name='delete',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    doc_name='storage pool',
)

__all__ = [
    'delete',
]
