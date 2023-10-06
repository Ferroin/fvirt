# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Domain related commands for the fvirt CLI interface.'''

from __future__ import annotations

from .._base.group import Group
from ...libvirt.domain import MATCH_ALIASES

domain = Group(
    name='domain',
    help='Perform various operations on libvirt domains.',
    callback=lambda x: None,
    lazy_commands={
        'autostart': 'fvirt.commands.domain.autostart.autostart',
        'create': 'fvirt.commands.domain.create.create',
        'define': 'fvirt.commands.domain.define.define',
        'list': 'fvirt.commands.domain.list.list_domains',
        'reset': 'fvirt.commands.domain.reset.reset',
        'shutdown': 'fvirt.commands.domain.shutdown.shutdown',
        'start': 'fvirt.commands.domain.start.start',
        'stop': 'fvirt.commands.domain.stop.stop',
        'undefine': 'fvirt.commands.domain.undefine.undefine',
        'xslt': 'fvirt.commands.domain.xslt.xslt',
    },
    aliases=MATCH_ALIASES,
)

__all__ = [
    'domain',
]
