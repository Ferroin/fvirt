# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for dumping info for a domain.'''

from __future__ import annotations

from .list import COLUMNS
from .._base.info import InfoCommand, InfoItem
from ...util.tables import color_optional

INFO_ITEMS = (
    InfoItem(name='Name', prop='name'),
    InfoItem(name='UUID', prop='uuid'),
    InfoItem(name='Generation ID', prop='genid', color=COLUMNS['genid'].color),
    InfoItem(name='Domain ID', prop='id', color=COLUMNS['id'].color),
    InfoItem(name='State', prop='state', color=COLUMNS['state'].color),
    InfoItem(name='Persistent', prop='persistent', color=COLUMNS['persistent'].color),
    InfoItem(name='Autostart', prop='autostart', color=COLUMNS['autostart'].color),
    InfoItem(name='Has Managed Save State', prop='hasManagedSave', color=COLUMNS['managed-save'].color),
    InfoItem(name='Has Current Snapshot', prop='hasCurrentSnapshot', color=COLUMNS['current-snapshot'].color),
    InfoItem(name='Guest OS Type', prop='osType', color=COLUMNS['osType'].color),
    InfoItem(name='Guest CPU Architecture', prop='osArch', color=COLUMNS['osArch'].color),
    InfoItem(name='Guest Machine Type', prop='osMatchine', color=COLUMNS['osMachine'].color),
    InfoItem(name='Emulator Binary', prop='emulator', color=COLUMNS['emulator'].color),
    InfoItem(name='Current Virtual CPUs', prop='currentCPUs', color=color_optional),
    InfoItem(name='Current Memory', prop='currentMemory', color=color_optional),
    InfoItem(name='Domain Title', prop='title'),
)

info = InfoCommand(
    name='info',
    info_items=INFO_ITEMS,
    hvprop='domains',
    doc_name='domain',
)

__all__ = [
    'info',
]
