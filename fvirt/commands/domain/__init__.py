# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Domain related commands for the fvirt CLI interface.'''

from __future__ import annotations

from typing import Final

from .._base.group import Group
from ...libvirt.domain import MATCH_ALIASES

domain: Final = Group(
    name='domain',
    help='Perform various operations on libvirt domains.',
    callback=lambda x: None,
    lazy_commands={
        'autostart': 'fvirt.commands.domain.autostart.autostart',
        'console': 'fvirt.commands.domain.console.console',
        'info': 'fvirt.commands.domain.info.info',
        'list': 'fvirt.commands.domain.list.list_domains',
        'new': 'fvirt.commands.domain.new.new',
        'reset': 'fvirt.commands.domain.reset.reset',
        'save': 'fvirt.commands.domain.save.save',
        'shutdown': 'fvirt.commands.domain.shutdown.shutdown',
        'start': 'fvirt.commands.domain.start.start',
        'stop': 'fvirt.commands.domain.stop.stop',
        'undefine': 'fvirt.commands.domain.undefine.undefine',
        'xml': 'fvirt.commands.domain.xml.xml',
        'xslt': 'fvirt.commands.domain.xslt.xslt',
    },
    aliases=MATCH_ALIASES,
)

__all__ = [
    'domain',
]
