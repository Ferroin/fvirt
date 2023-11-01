# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping info for a pool.'''

from __future__ import annotations

from typing import Final, final

from .list import COLUMNS
from .._base.info import InfoCommand, InfoItem
from .._base.objects import StoragePoolMixin

INFO_ITEMS: Final = (
    InfoItem(name='Name', prop='name'),
    InfoItem(name='UUID', prop='uuid'),
    InfoItem(name='State', prop='state', color=COLUMNS['state'].color),
    InfoItem(name='Persistent', prop='persistent', color=COLUMNS['persistent'].color),
    InfoItem(name='Autostart', prop='autostart', color=COLUMNS['autostart'].color),
    InfoItem(name='Pool Type', prop='type', color=COLUMNS['type'].color),
    InfoItem(name='Pool Format', prop='format', color=COLUMNS['format'].color),
    InfoItem(name='Pool Directory', prop='dir', color=COLUMNS['dir'].color),
    InfoItem(name='Pool Device', prop='device', color=COLUMNS['device'].color),
    InfoItem(name='Pool Target', prop='target', color=COLUMNS['target'].color),
    InfoItem(name='Volumes', prop='num_volumes', color=COLUMNS['volumes'].color),
    InfoItem(name='Total Capacity', prop='capacity', color=COLUMNS['capacity'].color, use_units=True),
    InfoItem(name='Allocated Space', prop='allocated', color=COLUMNS['allocated'].color, use_units=True),
    InfoItem(name='Available Space', prop='available', color=COLUMNS['available'].color, use_units=True),
)


@final
class _PoolInfo(InfoCommand, StoragePoolMixin):
    pass


info: Final = _PoolInfo(
    name='info',
    info_items=INFO_ITEMS,
)

__all__ = [
    'info',
]
