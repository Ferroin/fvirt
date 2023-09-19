# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Individual commands for the virshx CLI interface.'''

from .domains import domains
from .start import start
from .stop import stop
from .shutdown import shutdown
from .reset import reset

from .pools import pools
from .start_pool import start_pool
from .stop_pool import stop_pool

from .volumes import volumes

from .uri import uri

COMMANDS = [
    domains,
    reset,
    shutdown,
    start,
    start_pool,
    stop,
    stop_pool,
    pools,
    volumes,
    uri,
]

__all__ = [
    'COMMANDS',
]
