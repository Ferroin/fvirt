# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to wipe volumes.'''

from __future__ import annotations

from typing import Final, Self, final

from ._mixin import VolumeMixin
from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand


@final
class _WipeCommand(SimpleLifecycleCommand, VolumeMixin):
    '''Class for wiping volumes.'''
    @property
    def METHOD(self: Self) -> str: return 'wipe'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='wipe',
            continuous='wiping',
            past='wiped',
            idempotent_state='',
        )


wipe: Final = _WipeCommand(
    name='wipe',
)

__all__ = [
    'wipe',
]
