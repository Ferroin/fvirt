# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to undefine storage pools.'''

from __future__ import annotations

from ...libvirt.storage_pool import MATCH_ALIASES

from .._base.lifecycle import UndefineCommand

undefine = UndefineCommand(
    name='undefine',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    doc_name='storage pool',
)

__all__ = [
    'undefine',
]
