# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to an XSLT document to a group of domains.'''

from __future__ import annotations

from ...libvirt.domain import MATCH_ALIASES
from ...util.commands import make_xslt_command

xslt = make_xslt_command(
    name='xslt',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    hvnameprop='domains_by_name',
    doc_name='domain',
)

__all__ = [
    'xslt'
]
