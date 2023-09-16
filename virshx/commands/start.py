# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start domains.'''

from __future__ import annotations

from ._common import make_start_command
from ..libvirt.domain import MATCH_ALIASES

start = make_start_command(
    name='start',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    hvnameprop='domains_by_name',
    doc_name='domain',
)

__all__ = [
    'start',
]
