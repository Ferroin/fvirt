# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to define a new domain.'''

from __future__ import annotations

from typing import Final

from .._base.lifecycle import DefineCommand

define: Final = DefineCommand(
    name='define',
    method='defineDomain',
    doc_name='domain',
)

__all__ = [
    'define',
]
