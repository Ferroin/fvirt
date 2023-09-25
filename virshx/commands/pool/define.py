# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to define a new storage pool.'''

from __future__ import annotations

from ...util.commands import make_define_command

define = make_define_command(
    name='define',
    define_method='defineStoragePool',
    doc_name='storage pool',
)

__all__ = [
    'define',
]
