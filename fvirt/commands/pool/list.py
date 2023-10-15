# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from typing import Final

from .._base.list import ListCommand
from ...libvirt.storage_pool import MATCH_ALIASES
from ...util.tables import Column, color_bool
from ...util.terminal import get_terminal

EPILOG: Final = '''
For performance reasons, information about the volumes in any given
storage pool is cached by the libvirt daemon. This information is only
updated when a pool is started (or created), when certain operations
(such as defining or deleting volumes) occur, and when the pool is
explicitly refreshed.

This is usually not an issue as the libvirt daemon tracks any changes
made through it, but if some external tool modifies the underlying
storage of the pool, the information shown by this command may not be
accurate any more.

To explicitly refresh the information about the volumes in a storage pool,
use the 'fvirt pool refresh' command.
'''.lstrip().rstrip()


def color_state(value: bool) -> str:
    '''Apply colors to a pool state.'''
    if value:
        return get_terminal().bright_green_on_black('running')
    else:
        return 'inactive'


COLUMNS: Final = {
    'name': Column(title='Name', prop='name'),
    'uuid': Column(title='UUID', prop='uuid'),
    'state': Column(title='State', prop='running', color=color_state),
    'persistent': Column(title='Persistent', prop='persistent', color=color_bool),
    'autostart': Column(title='Autostart', prop='autostart', color=color_bool),
    'volumes': Column(title='Volumes', prop='numVolumes', right_align=True),
    'capacity': Column(title='Capacity', prop='capacity', right_align=True),
    'allocated': Column(title='Allocated', prop='allocated', right_align=True),
    'available': Column(title='Available', prop='available', right_align=True),
    'type': Column(title='Type', prop='type'),
    'format': Column(title='Format', prop='format'),
    'dir': Column(title='Directory', prop='dir'),
    'device': Column(title='Device', prop='device'),
    'target': Column(title='Target', prop='target'),
}

DEFAULT_COLS: Final = (
    'name',
    'type',
    'format',
    'state',
    'autostart',
    'volumes',
    'capacity',
    'available',
)

list_pools: Final = ListCommand(
    name='list',
    aliases=MATCH_ALIASES,
    columns=COLUMNS,
    default_cols=DEFAULT_COLS,
    hvprop='pools',
    doc_name='storage pool',
)

__all__ = [
    'list_pools',
]
