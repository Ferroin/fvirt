# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to dump the XML config of a pool.'''

from __future__ import annotations

from typing import Final, final

from .._base.objects import StoragePoolMixin
from .._base.xml import XMLCommand


@final
class _PoolXML(XMLCommand, StoragePoolMixin):
    pass


xml: Final = _PoolXML(
    name='xml',
)

__all__ = [
    'xml'
]
