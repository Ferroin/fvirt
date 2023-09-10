# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Individual commands for the virshx CLI interface.'''

from .domains import domains
from .uri import uri

COMMANDS = [
    uri,
    domains,
]

__all__ = [
    'COMMANDS',
]
