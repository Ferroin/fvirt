# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start storage pools.'''

from __future__ import annotations

from typing import Final

from .._base.lifecycle import StartCommand
from ...libvirt.storage_pool import MATCH_ALIASES

start: Final = StartCommand(
    name='start',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    doc_name='storage pool',
)

__all__ = [
    'start',
]
