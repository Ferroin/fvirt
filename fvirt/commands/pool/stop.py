# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to stop storage pools.'''

from __future__ import annotations

from .._base.lifecycle import StopCommand
from ...libvirt.storage_pool import MATCH_ALIASES

stop = StopCommand(
    name='stop',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    doc_name='storage pool',
)

__all__ = [
    'stop',
]
