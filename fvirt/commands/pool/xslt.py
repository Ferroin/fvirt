# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to apply an XSLT document to a group of storage pools.'''

from __future__ import annotations

from typing import Final

from .._base.xslt import XSLTCommand
from ...libvirt.storage_pool import MATCH_ALIASES

xslt: Final = XSLTCommand(
    name='xslt',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    metavar='POOL',
    doc_name='storage pool',
)

__all__ = [
    'xslt'
]
