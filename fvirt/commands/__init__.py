# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Individual commands for the fvirt CLI interface.'''

from __future__ import annotations

from typing import Final

LAZY_COMMANDS: Final = {
    'config': 'fvirt.commands.config.config',
    'domain': 'fvirt.commands.domain.domain',
    'host': 'fvirt.commands.host.host',
    'pool': 'fvirt.commands.pool.pool',
    'schema': 'fvirt.commands.schema.schema',
    'version': 'fvirt.commands.version.version',
    'volume': 'fvirt.commands.volume.volume',
}

__all__ = [
    'LAZY_COMMANDS',
]
