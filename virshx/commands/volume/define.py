# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to define a new volume.'''

from __future__ import annotations

from ...util.commands import make_define_command

define = make_define_command(
    name='define',
    define_method='defineVolume',
    doc_name='volume',
    parent='pools',
    parent_name='storage pool',
    ctx_key='pool',
)

__all__ = [
    'define',
]
