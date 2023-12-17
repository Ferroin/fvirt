# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Terminal handling for the fvirt CLI.'''

from __future__ import annotations

import functools
import logging

from typing import Final

import blessed

LOGGER: Final = logging.getLogger(__name__)


@functools.cache
def get_terminal() -> blessed.Terminal:
    '''Return a blessed.Terminal instance.

       A function is used here so that we can defer initializing the
       object until it}s actually needed, which saves significant time
       on startup because most things don't use it.

       The return value is cached so that only a single instance is
       ever used.'''
    LOGGER.debug('Initializing terminal interface.')

    return blessed.Terminal()


__all__ = [
    'get_terminal',
]
