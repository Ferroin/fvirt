# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Individual commands for the virshx CLI interface.'''

from .domain import COMMANDS as DOMAIN_COMMANDS
from .pool import COMMANDS as POOL_COMMANDS

from .volumes import volumes

from .uri import uri

COMMANDS = [
    uri,
    volumes,
]

COMMANDS += DOMAIN_COMMANDS
COMMANDS += POOL_COMMANDS

__all__ = [
    'COMMANDS',
]
