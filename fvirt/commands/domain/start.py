# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start domains.'''

from __future__ import annotations

from .._base.lifecycle import StartCommand
from ...libvirt.domain import MATCH_ALIASES

start = StartCommand(
    name='start',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    doc_name='domain',
)

__all__ = [
    'start',
]
