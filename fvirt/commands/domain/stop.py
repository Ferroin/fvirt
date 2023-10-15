# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to stop domains.'''

from __future__ import annotations

from typing import Final

from .._base.lifecycle import StopCommand
from ...libvirt.domain import MATCH_ALIASES

stop: Final = StopCommand(
    name='stop',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    doc_name='domain',
)

__all__ = [
    'stop',
]
