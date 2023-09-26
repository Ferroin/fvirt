# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to undefine domains.'''

from __future__ import annotations

from ...libvirt.domain import MATCH_ALIASES
from ...util.commands import make_undefine_command

undefine = make_undefine_command(
    name='undefine',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    hvnameprop='domains_by_name',
    doc_name='domain',
)

__all__ = [
    'undefine',
]
