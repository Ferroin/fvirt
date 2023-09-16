# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to stop domains.'''

from __future__ import annotations

from ._common import make_stop_command
from ..libvirt.domain import MATCH_ALIASES

stop = make_stop_command(
    name='stop',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    hvnameprop='domains_by_name',
    doc_name='domain',
)

__all__ = [
    'stop',
]
