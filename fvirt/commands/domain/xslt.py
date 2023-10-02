# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to an XSLT document to a group of domains.'''

from __future__ import annotations

from .._base.xslt import XSLTCommand

from ...libvirt.domain import MATCH_ALIASES

xslt = XSLTCommand(
    name='xslt',
    aliases=MATCH_ALIASES,
    hvprop='domains',
    metavar='DOMAIN',
    doc_name='domain',
)

__all__ = [
    'xslt'
]
