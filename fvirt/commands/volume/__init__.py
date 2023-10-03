# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Volume related commands for the fvirt CLI interface.'''

from __future__ import annotations

from .define import define
from .list import list_volumes
from .._base.group import Group
from ...libvirt.volume import MATCH_ALIASES

volume = Group(
    name='volume',
    help='Perform various operations on libvirt volumes.',
    callback=lambda x: None,
    commands=(
        define,
        list_volumes,
    ),
    aliases=MATCH_ALIASES,
)

__all__ = [
    'volume',
]
