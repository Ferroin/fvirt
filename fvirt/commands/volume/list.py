# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from typing import Final

from .._base.list import ListCommand
from ...libvirt.volume import MATCH_ALIASES
from ...util.tables import Column

COLUMNS: Final = {
    'name': Column(title='Name', prop='name'),
    'key': Column(title='Key', prop='key'),
    'type': Column(title='Type', prop='type'),
    'format': Column(title='Format', prop='format'),
    'path': Column(title='Path', prop='path'),
    'capacity': Column(title='Capacity', prop='capacity', right_align=True),
    'allocated': Column(title='Allocated', prop='allocated', right_align=True),
}

DEFAULT_COLS: Final = (
    'name',
    'path',
    'capacity',
)

list_volumes: Final = ListCommand(
    name='list',
    aliases=MATCH_ALIASES,
    columns=COLUMNS,
    default_cols=DEFAULT_COLS,
    hvprop='pools',
    hvmetavar='POOL',
    obj_prop='volumes',
    doc_name='volume',
    obj_name='storage pool',
    single_list_props=(
        'name',
        'key',
    ),
)

__all__ = [
    'list_volumes',
]
