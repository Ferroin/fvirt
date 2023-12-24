# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to build storage pools.'''

from __future__ import annotations

from typing import Final, Self, final

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from .._base.objects import StoragePoolMixin


@final
class _BuildCommand(SimpleLifecycleCommand, StoragePoolMixin):
    '''Class for building storage pools.'''
    @property
    def METHOD(self: Self) -> str: return 'build'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='build',
            continuous='building',
            past='built',
            idempotent_state='',
        )


build: Final = _BuildCommand(
    name='build',
)

__all__ = [
    'build',
]
