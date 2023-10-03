# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Individual commands for the fvirt CLI interface.'''

from .domain import domain
from .pool import pool
from .uri import uri
from .volume import volume

COMMANDS = [
    domain,
    pool,
    uri,
    volume,
]

__all__ = [
    'COMMANDS',
]
