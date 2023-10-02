# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Storage pool related commands for the fvirt CLI interface.'''

from __future__ import annotations

from .define import define
from .list import list_pools
from .start import start
from .stop import stop
from .undefine import undefine
from .xslt import xslt

from .._base.group import Group

from ...libvirt.volume import MATCH_ALIASES

pool = Group(
    name='pool',
    doc_name='storage pool',
    help='Perform various operations on libvirt storage pools.',
    callback=lambda x: None,
    commands=(
        define,
        list_pools,
        start,
        stop,
        undefine,
        xslt,
    ),
    aliases=MATCH_ALIASES,
)

__all__ = [
    'pool',
]
