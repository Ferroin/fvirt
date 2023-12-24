# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to reset domains.'''

from __future__ import annotations

from typing import Final, Self, final

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from .._base.objects import DomainMixin


@final
class _ResetCommand(SimpleLifecycleCommand, DomainMixin):
    '''Class for resetting domains.'''
    @property
    def METHOD(self: Self) -> str: return 'reset'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='reset',
            continuous='resetting',
            past='reset',
            idempotent_state='',
        )


reset: Final = _ResetCommand(
    name='reset',
)

__all__ = [
    'reset',
]
