# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Domain related commands for the fvirt CLI interface.'''

from __future__ import annotations

from .create import create
from .define import define
from .list import list_domains
from .reset import reset
from .shutdown import shutdown
from .start import start
from .stop import stop
from .undefine import undefine
from .xslt import xslt
from .._base.group import Group
from ...libvirt.domain import MATCH_ALIASES

domain = Group(
    name='domain',
    help='Perform various operations on libvirt domains.',
    callback=lambda x: None,
    commands=(
        create,
        define,
        list_domains,
        reset,
        shutdown,
        start,
        stop,
        undefine,
        xslt,
    ),
    aliases=MATCH_ALIASES,
)

__all__ = [
    'domain',
]
