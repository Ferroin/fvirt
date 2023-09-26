# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Individual commands for the fvirt CLI interface.'''

from .domain import domain
from .pool import pool
from .volume import volume

from .uri import uri

COMMANDS = [
    domain,
    pool,
    uri,
    volume,
]

__all__ = [
    'COMMANDS',
]
