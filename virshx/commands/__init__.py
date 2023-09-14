# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Individual commands for the virshx CLI interface.'''

from .domains import domains
from .start import start

from .pools import pools
from .start_pool import start_pool

from .volumes import volumes

from .uri import uri

COMMANDS = [
    uri,
    domains,
    start,
    start_pool,
    pools,
    volumes,
]

__all__ = [
    'COMMANDS',
]
