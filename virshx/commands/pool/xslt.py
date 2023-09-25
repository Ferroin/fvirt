# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to apply an XSLT document to a group of storage pools.'''

from __future__ import annotations

from ...libvirt.storage_pool import MATCH_ALIASES
from ...util.commands import make_xslt_command

xslt = make_xslt_command(
    name='xslt',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    hvnameprop='pools_by_name',
    doc_name='storage pool',
)

__all__ = [
    'xslt'
]
