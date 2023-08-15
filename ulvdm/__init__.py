# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''ulvdm: A minimal wrapper around libvirt to supplement virsh.'''

import sys

VERSION = (0, 0, 1)

if not sys.version_info >= (3, 10):
    raise RuntimeError('ulvdm requires Python 3.10 or newer.')
