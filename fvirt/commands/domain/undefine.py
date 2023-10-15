# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to undefine domains.'''

from __future__ import annotations

from typing import Final

from .._base.lifecycle import UndefineCommand
from ...libvirt.domain import MATCH_ALIASES

undefine: Final = UndefineCommand(
    name='undefine',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    doc_name='domain',
)

__all__ = [
    'undefine',
]
