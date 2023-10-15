# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to define a new volume.'''

from __future__ import annotations

from typing import Final

from .._base.lifecycle import DefineCommand

define: Final = DefineCommand(
    name='define',
    method='defineVolume',
    doc_name='volume',
    parent='pools',
    parent_name='storage pool',
    parent_metavar='POOL',
)

__all__ = [
    'define',
]
