# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to refresh storage pools.'''

from __future__ import annotations

from typing import Final, Self, final

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from ...libvirt.storage_pool import MATCH_ALIASES


@final
class _RefreshCommand(SimpleLifecycleCommand):
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
    aliases=MATCH_ALIASES,
    hvprop='pools',
    doc_name='storage pool',
)

__all__ = [
    'refresh',
]
