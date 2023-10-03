# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from .._base.list import ListCommand
from ...libvirt.storage_pool import MATCH_ALIASES
from ...util.tables import Column, color_bool
from ...util.terminal import get_terminal


def color_state(value: bool) -> str:
    '''Apply colors to a pool state.'''
    if value:
        return get_terminal().bright_green_on_black('running')
    else:
        return 'inactive'


COLUMNS = {
    'name': Column(title='Name', prop='name'),
    'uuid': Column(title='UUID', prop='uuid'),
    'state': Column(title='State', prop='running', color=color_state),
    'persistent': Column(title='Persistent', prop='persistent', color=color_bool),
    'autostart': Column(title='Autostart', prop='autostart', color=color_bool),
    'volumes': Column(title='Volumes', prop='numVolumes', right_align=True),
    'capacity': Column(title='Capacity', prop='capacity', right_align=True),
    'allocation': Column(title='Allocation', prop='allocation', right_align=True),
    'available': Column(title='Available', prop='available', right_align=True),
    'type': Column(title='Type', prop='type'),
    'format': Column(title='Format', prop='format'),
    'dir': Column(title='Directory', prop='dir'),
    'device': Column(title='Device', prop='device'),
    'target': Column(title='Target', prop='target'),
}

DEFAULT_COLS = (
    'name',
    'type',
    'format',
    'state',
    'autostart',
    'volumes',
    'capacity',
    'available',
)

list_pools = ListCommand(
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
