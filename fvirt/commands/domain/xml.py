# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to dump the XML config of a domain.'''

from __future__ import annotations

from typing import Final

from .._base.xml import XMLCommand

xml: Final = XMLCommand(
    name='xml',
    hvprop='domains',
    metavar='DOMAIN',
    doc_name='domain',
)

__all__ = [
    'xml'
]
