# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to list storage pools.'''

from __future__ import annotations

from typing import Final, final

from .._base.list import ListCommand
from .._base.objects import VolumeMixin
from ...libvirt.volume import MATCH_ALIASES
from ...util.tables import Column, color_optional

COLUMNS: Final = {
    'name': Column(title='Name', prop='name'),
    'key': Column(title='Key', prop='key'),
    'type': Column(title='Type', prop='vol_type'),
    'format': Column(title='Format', prop='format'),
    'path': Column(title='Path', prop='path', color=color_optional),
    'capacity': Column(title='Capacity', prop='capacity', right_align=True, use_units=True),
    'allocated': Column(title='Allocated', prop='allocated', right_align=True, use_units=True),
}

DEFAULT_COLS: Final = (
    'name',
    'path',
    'capacity',
)

SIMPLE_LIST_PROPS = (
    'name',
    'key',
)


@final
class _VolList(ListCommand, VolumeMixin):
    pass


list_volumes: Final = _VolList(
    name='list',
    aliases=MATCH_ALIASES,
    columns=COLUMNS,
    default_cols=DEFAULT_COLS,
    single_list_props=SIMPLE_LIST_PROPS
)

__all__ = [
    'list_volumes',
]
