# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Volume related commands for the fvirt CLI interface.'''

from __future__ import annotations

from .._base.group import Group
from ...libvirt.volume import MATCH_ALIASES

volume = Group(
    name='volume',
    help='Perform various operations on libvirt volumes.',
    callback=lambda x: None,
    lazy_commands={
        'define': 'fvirt.commands.volume.define.define',
        'delete': 'fvirt.commands.volume.delete.delete',
        'list': 'fvirt.commands.volume.list.list_volumes',
        'xml': 'fvirt.commands.volume.xml.xml',
    },
    aliases=MATCH_ALIASES,
)

__all__ = [
    'volume',
]
