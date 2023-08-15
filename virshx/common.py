# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Common functions and definitions used throughout virshx.'''

from __future__ import annotations

import re

VERSION = (0, 0, 1)


class VirshxException(Exception):
    '''Base exception for all virshx exceptions.'''
    pass


def name_match(name: str, pattern: str | re.Pattern) -> bool:
    '''Determine if a name matches a given pattern.

       Accepts a string pattern or a re.Pattern object.'''
    match re.match(pattern, name):
        case None:
            return False
        case _:
            return True


__all__ = [
    'VERSION',
    'VirshxException',
    'name_match',
]
