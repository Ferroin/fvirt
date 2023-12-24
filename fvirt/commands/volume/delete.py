# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to delete volumes.'''

from __future__ import annotations

from typing import Final, Self, final

from ._mixin import VolumeMixin
from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand


@final
class _VolDelete(SimpleLifecycleCommand, VolumeMixin):
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


delete: Final = _VolDelete(
    name='delete',
)

__all__ = [
    'delete',
]
