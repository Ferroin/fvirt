# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start storage pools.'''

from __future__ import annotations

from ._common import make_start_command
from ..libvirt.storage_pool import MATCH_ALIASES

start_pool = make_start_command(
    name='start-pool',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    hvnameprop='pools_by_name',
    doc_name='storage pool',
)

__all__ = [
    'start_pool',
]
