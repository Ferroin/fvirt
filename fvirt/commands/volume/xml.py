# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to dump the XML config of a volume.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import VolumeMixin
from .._base.xml import XMLCommand


@final
class _VolXML(XMLCommand, VolumeMixin):
    pass


xml: Final = _VolXML(
    name='xml',
)

__all__ = [
    'xml'
]
