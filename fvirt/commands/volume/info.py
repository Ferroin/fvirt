# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping info for a volume.'''

from __future__ import annotations

from typing import Final, final

from .list import COLUMNS
from .._base.info import InfoCommand, InfoItem
from .._base.objects import VolumeMixin

INFO_ITEMS: Final = (
    InfoItem(name='Name', prop='name'),
    InfoItem(name='Key', prop='key'),
    InfoItem(name='Volume Type', prop='type', color=COLUMNS['type'].color),
    InfoItem(name='Volume Format', prop='format', color=COLUMNS['format'].color),
    InfoItem(name='Volume Path', prop='path', color=COLUMNS['path'].color),
    InfoItem(name='Total Capacity', prop='capacity', color=COLUMNS['capacity'].color),
    InfoItem(name='Allocated Space', prop='allocated', color=COLUMNS['allocated'].color),
)


@final
class _VolInfo(InfoCommand, VolumeMixin):
    pass


info: Final = _VolInfo(
    name='info',
    info_items=INFO_ITEMS,
)

__all__ = [
    'info',
]
