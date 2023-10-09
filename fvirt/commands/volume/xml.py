# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to dump the XML config of a volume.'''

from __future__ import annotations

from .._base.xml import XMLCommand

xml = XMLCommand(
    name='xml',
    hvprop='pools',
    metavar='VOLUME',
    doc_name='volume',
    parent_prop='volumes',
    parent_name='storage pool',
    parent_metavar='POOL',
)

__all__ = [
    'xml'
]
