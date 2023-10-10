# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Individual commands for the fvirt CLI interface.'''

LAZY_COMMANDS = {
    'domain': 'fvirt.commands.domain.domain',
    'host': 'fvirt.commands.host.host',
    'pool': 'fvirt.commands.pool.pool',
    'version': 'fvirt.commands.version.version',
    'volume': 'fvirt.commands.volume.volume',
}

__all__ = [
    'LAZY_COMMANDS',
]
