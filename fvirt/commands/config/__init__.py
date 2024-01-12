# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Commands that work with fvirt’s configuration.'''

from __future__ import annotations

from typing import Final

from .._base.group import Group

config: Final = Group(
    name='config',
    help='View and work with the configuration for fvirt.',
    callback=lambda x: None,
    lazy_commands={
        'dump': 'fvirt.commands.config.dump.dump',
        'effective': 'fvirt.commands.config.effective.effective',
        'paths': 'fvirt.commands.config.paths.paths',
    },
)

__all__ = [
    'config',
]
