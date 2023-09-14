# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Individual commands for the virshx CLI interface.'''

from .domains import domains
from .start import start

from .pools import pools

from .volumes import volumes

from .uri import uri

COMMANDS = [
    uri,
    domains,
    start,
    pools,
    volumes,
]

__all__ = [
    'COMMANDS',
]
