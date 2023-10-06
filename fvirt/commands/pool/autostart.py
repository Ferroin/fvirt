# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to set the autostart state for one or more storage pools.'''

from __future__ import annotations

from .._base.autostart import AutostartCommand
from ...libvirt.storage_pool import MATCH_ALIASES

autostart = AutostartCommand(
    name='autostart',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    doc_name='storage pool',
)

__all__ = (
    'autostart',
)
