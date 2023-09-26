# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to undefine storage pools.'''

from __future__ import annotations

from ...libvirt.storage_pool import MATCH_ALIASES
from ...util.commands import make_undefine_command

undefine = make_undefine_command(
    name='undefine',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    hvnameprop='pools_by_name',
    doc_name='storage pool',
)

__all__ = [
    'undefine',
]
