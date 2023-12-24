# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import StoragePoolMixin
from .._base.list import ListCommand
from .._base.tables import Column, color_bool, color_optional
from .._base.terminal import get_terminal
from ...libvirt.storage_pool import StoragePoolState

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


def color_state(value: StoragePoolState) -> str:
    '''Apply colors to a pool state.'''
    TERM = get_terminal()

    match value:
        case s if s in {StoragePoolState.RUNNING}:
            return TERM.bright_green_on_black(str(value))
        case s if s in {StoragePoolState.BUILDING}:
            return TERM.bright_yellow_on_black(str(value))
        case s if s in {StoragePoolState.DEGRADED, StoragePoolState.INACCESSIBLE}:
            return TERM.bright_red_on_black(str(value))
        case _:
            return str(value)

    raise RuntimeError  # Needed because mypy thinks the above case statement is non-exhaustive.


COLUMNS: Final = {
    'name': Column(title='Name', prop='name'),
    'uuid': Column(title='UUID', prop='uuid'),
    'state': Column(title='State', prop='state', color=color_state),
    'persistent': Column(title='Persistent', prop='persistent', color=color_bool),
    'autostart': Column(title='Autostart', prop='autostart', color=color_bool),
    'volumes': Column(title='Volumes', prop='num_volumes', right_align=True, color=color_optional),
    'capacity': Column(title='Capacity', prop='capacity', right_align=True, color=color_optional, use_units=True),
    'allocated': Column(title='Allocated', prop='allocated', right_align=True, color=color_optional, use_units=True),
    'available': Column(title='Available', prop='available', right_align=True, color=color_optional, use_units=True),
    'type': Column(title='Type', prop='pool_type', color=color_optional),
    'format': Column(title='Format', prop='format', color=color_optional),
    'dir': Column(title='Directory', prop='dir', color=color_optional),
    'device': Column(title='Device', prop='device', color=color_optional),
    'target': Column(title='Target', prop='target', color=color_optional),
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


@final
class _PoolList(ListCommand, StoragePoolMixin):
    pass


list_pools: Final = _PoolList(
    name='list',
    columns=COLUMNS,
    default_cols=DEFAULT_COLS,
)

__all__ = [
    'list_pools',
]
