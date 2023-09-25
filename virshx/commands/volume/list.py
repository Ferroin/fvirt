# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from ...libvirt.volume import MATCH_ALIASES
from ...util.commands import make_sub_list_command
from ...util.tables import Column

COLUMNS = {
    'name': Column(title='Name', prop='name'),
    'key': Column(title='Key', prop='key'),
    'type': Column(title='Type', prop='type'),
    'format': Column(title='Format', prop='format'),
    'path': Column(title='Path', prop='path'),
    'capacity': Column(title='Capacity', prop='capacity', right_align=True),
    'allocation': Column(title='Allocation', prop='allocation', right_align=True),
}

DEFAULT_COLS = [
    'name',
    'path',
    'capacity',
]

list_volumes = make_sub_list_command(
    name='list',
    aliases=MATCH_ALIASES,
    columns=COLUMNS,
    default_cols=DEFAULT_COLS,
    hvprop='pools',
    objprop='volumes',
    ctx_key='pool',
    doc_name='volume',
    obj_doc_name='storage pool',
)

__all__ = [
    'list_volumes',
]
