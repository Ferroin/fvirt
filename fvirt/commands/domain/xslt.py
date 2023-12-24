# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to an XSLT document to a group of domains.'''

from __future__ import annotations

from typing import Final, final

from ._mixin import DomainMixin
from .._base.xslt import XSLTCommand


@final
class _DomainXSLT(XSLTCommand, DomainMixin):
    pass


xslt: Final = _DomainXSLT(
    name='xslt',
)

__all__ = [
    'xslt'
]
