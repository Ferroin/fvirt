# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to dump the XML config of a domain.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import DomainMixin
from .._base.xml import XMLCommand


@final
class _DomainXML(XMLCommand, DomainMixin):
    pass


xml: Final = _DomainXML(
    name='xml',
)

__all__ = [
    'xml'
]
