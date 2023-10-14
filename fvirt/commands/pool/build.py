# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to build storage pools.'''

from __future__ import annotations

from typing import Self

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from ...libvirt.storage_pool import MATCH_ALIASES


class _BuildCommand(SimpleLifecycleCommand):
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


build = _BuildCommand(
    name='build',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    doc_name='storage pool',
)

__all__ = [
    'build',
]
