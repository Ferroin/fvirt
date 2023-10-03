# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Storage pool related commands for the fvirt CLI interface.'''

from __future__ import annotations

from .._base.group import Group
from ...libvirt.volume import MATCH_ALIASES

pool = Group(
    name='pool',
    doc_name='storage pool',
    help='Perform various operations on libvirt storage pools.',
    callback=lambda x: None,
    lazy_commands={
        'define': 'fvirt.commands.pool.define.define',
        'list': 'fvirt.commands.pool.list.list_pools',
        'start': 'fvirt.commands.pool.start.start',
        'stop': 'fvirt.commands.pool.stop.stop',
        'undefine': 'fvirt.commands.pool.undefine.undefine',
        'xslt': 'fvirt.commands.pool.xslt.xslt',
    },
    aliases=MATCH_ALIASES,
)

__all__ = [
    'pool',
]
