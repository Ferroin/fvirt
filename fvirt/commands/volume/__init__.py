# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Volume related commands for the fvirt CLI interface.'''

from __future__ import annotations

from typing import Final

from .._base.group import Group
from ...libvirt.volume import MATCH_ALIASES

volume: Final = Group(
    name='volume',
    help='Perform various operations on libvirt volumes.',
    callback=lambda x: None,
    lazy_commands={
        'define': 'fvirt.commands.volume.define.define',
        'delete': 'fvirt.commands.volume.delete.delete',
        'download': 'fvirt.commands.volume.download.download',
        'info': 'fvirt.commands.volume.info.info',
        'list': 'fvirt.commands.volume.list.list_volumes',
        'upload': 'fvirt.commands.volume.upload.upload',
        'xml': 'fvirt.commands.volume.xml.xml',
        'wipe': 'fvirt.commands.volume.wipe.wipe',
    },
    aliases=MATCH_ALIASES,
)

__all__ = [
    'volume',
]
