# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to dump the XML config of a pool.'''

from __future__ import annotations

from .._base.xml import XMLCommand

xml = XMLCommand(
    name='xml',
    hvprop='pools',
    metavar='POOL',
    doc_name='storage pool',
)

__all__ = [
    'xml'
]