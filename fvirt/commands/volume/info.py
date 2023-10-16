# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping info for a volume.'''

from __future__ import annotations

from .list import COLUMNS
from .._base.info import InfoCommand, InfoItem

INFO_ITEMS = (
    InfoItem(name='Name', prop='name'),
    InfoItem(name='Key', prop='key'),
    InfoItem(name='Volume Type', prop='type', color=COLUMNS['type'].color),
    InfoItem(name='Volume Format', prop='format', color=COLUMNS['format'].color),
    InfoItem(name='Volume Path', prop='path', color=COLUMNS['path'].color),
    InfoItem(name='Total Capacity', prop='capacity', color=COLUMNS['capacity'].color),
    InfoItem(name='Allocated Space', prop='allocated', color=COLUMNS['allocated'].color),
)

info = InfoCommand(
    name='info',
    info_items=INFO_ITEMS,
    hvprop='pools',
    doc_name='volume',
    parent='volumes',
    parent_name='storage pool',
    parent_metavar='POOL',
)

__all__ = [
    'info',
]
