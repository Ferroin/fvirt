# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to wipe volumes.'''

from __future__ import annotations

from typing import Final, Self, final

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from .._base.objects import VolumeMixin
from ...libvirt.volume import MATCH_ALIASES


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
    aliases=MATCH_ALIASES,
)

__all__ = [
    'wipe',
]
