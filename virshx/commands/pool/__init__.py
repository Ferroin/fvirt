# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Storage pool related commands for the virshx CLI interface.'''

from .pools import pools
from .start_pool import start_pool
from .stop_pool import stop_pool
from .xslt_pool import xslt_pool

COMMANDS = [
    pools,
    start_pool,
    stop_pool,
    xslt_pool,
]

__all__ = [
    'COMMANDS',
]
