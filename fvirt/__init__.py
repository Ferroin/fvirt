# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''fvirt: A lightweight frontend for libvirt.'''

import sys

from .version import VERSION

if not sys.version_info >= (3, 11):
    raise RuntimeError('fvirt requires Python 3.11 or newer.')

__all__ = [
    'VERSION',
]
