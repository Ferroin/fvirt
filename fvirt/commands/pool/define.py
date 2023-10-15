# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to define a new storage pool.'''

from __future__ import annotations

from typing import Final

from .._base.lifecycle import DefineCommand

define: Final = DefineCommand(
    name='define',
    method='defineStoragePool',
    doc_name='storage pool',
)

__all__ = [
    'define',
]
