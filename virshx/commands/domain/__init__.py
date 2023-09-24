# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Domain related commands for the virshx CLI interface.'''

from .domains import domains
from .start import start
from .stop import stop
from .shutdown import shutdown
from .reset import reset
from .xslt import xslt

COMMANDS = [
    domains,
    start,
    stop,
    shutdown,
    reset,
    xslt,
]

__all__ = [
    'COMMANDS',
]
