# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to apply an XSLT document to a group of storage pools.'''

from __future__ import annotations

from ._common import make_xslt_command
from ..libvirt.storage_pool import MATCH_ALIASES

xslt_pool = make_xslt_command(
    name='xslt-pool',
    aliases=MATCH_ALIASES,
    hvprop='pools',
    hvnameprop='pools_by_name',
    doc_name='storage pool',
)

__all__ = [
    'xslt_pool'
]
