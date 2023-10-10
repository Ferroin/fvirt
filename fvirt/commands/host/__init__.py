# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Host related commands for the fvirt CLI interface.'''

from __future__ import annotations

from .._base.group import Group

host = Group(
    name='host',
    help='Perform various operations on the libvirt host.',
    callback=lambda x: None,
    lazy_commands={
        'version': 'fvirt.commands.host.version.version',
        'uri': 'fvirt.commands.host.uri.uri',
    },
)

__all__ = [
    'host',
]
