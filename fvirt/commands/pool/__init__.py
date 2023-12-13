# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Storage pool related commands for the fvirt CLI interface.'''

from __future__ import annotations

from typing import Final

from .._base.group import Group
from ...libvirt.volume import MATCH_ALIASES

pool: Final = Group(
    name='pool',
    doc_name='storage pool',
    help='Perform various operations on libvirt storage pools.',
    callback=lambda x: None,
    lazy_commands={
        'autostart': 'fvirt.commands.pool.autostart.autostart',
        'build': 'fvirt.commands.pool.build.build',
        'delete': 'fvirt.commands.pool.delete.delete',
        'info': 'fvirt.commands.pool.info.info',
        'list': 'fvirt.commands.pool.list.list_pools',
        'new': 'fvirt.commands.pool.new.new',
        'refresh': 'fvirt.commands.pool.refresh.refresh',
        'start': 'fvirt.commands.pool.start.start',
        'stop': 'fvirt.commands.pool.stop.stop',
        'undefine': 'fvirt.commands.pool.undefine.undefine',
        'xml': 'fvirt.commands.pool.xml.xml',
        'xslt': 'fvirt.commands.pool.xslt.xslt',
    },
    aliases=MATCH_ALIASES,
)

__all__ = [
    'pool',
]
