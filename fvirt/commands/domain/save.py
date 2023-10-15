# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to trigger a managed save of a domain.'''

from __future__ import annotations

from typing import Final, Self, final

from .._base.lifecycle import OperationHelpInfo, SimpleLifecycleCommand
from ...libvirt.domain import MATCH_ALIASES

EXTRA_HELP: Final = '''
Saving a domain is conceptually equivalent to suspending it to disk,
without needing any support from the guest OS to handle this. Saving a
domain will suspend it’s execution, save it’s internal state to disk,
and then power off the domain itself. The next time the domain is started,
it will use that saved state to resume execution from when it was saved,
then discard the state on-disk.

Only persistent domains may be saved.
'''.lstrip().rstrip()


@final
class _SaveCommand(SimpleLifecycleCommand):
    '''Class for saving domains.'''
    @property
    def METHOD(self: Self) -> str: return 'managedSave'

    @property
    def OP_HELP(self: Self) -> OperationHelpInfo:
        return OperationHelpInfo(
            verb='save',
            continuous='saving',
            past='saved',
            idempotent_state='saved',
        )


save: Final = _SaveCommand(
    name='save',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    doc_name='domain',
    epilog=EXTRA_HELP,
)

__all__ = [
    'save',
]
