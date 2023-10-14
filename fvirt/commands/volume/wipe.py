# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to wipe volumes.'''

from __future__ import annotations

from typing import Self

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from ...libvirt.volume import MATCH_ALIASES


class _WipeCommand(SimpleLifecycleCommand):
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


wipe = _WipeCommand(
    name='wipe',
    aliases=MATCH_ALIASES,
    hvprop='volumes',
    doc_name='volume',
    parent='pools',
    parent_name='storage pool',
    parent_metavar='POOL',
)

__all__ = [
    'wipe',
]
