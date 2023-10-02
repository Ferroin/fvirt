# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start storage pools.'''

from __future__ import annotations

from ...libvirt.storage_pool import MATCH_ALIASES

from .._base.lifecycle import StartCommand

start = StartCommand(
    name='start',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    doc_name='storage pool',
)

__all__ = [
    'start',
]
