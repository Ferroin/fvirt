# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''virshx: A minimal wrapper around libvirt to supplement virsh.'''

import sys

from .common import VERSION

if not sys.version_info >= (3, 10):
    raise RuntimeError('virshx requires Python 3.10 or newer.')

__all__ = [
    'VERSION',
]
