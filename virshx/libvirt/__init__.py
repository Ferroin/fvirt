# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper classes for libvit.

  The official libvirt bindings for Python are essentially a 1:1 mapping
  of the C API. This leads to a lot of questionable behaviors such as
  returning None instead of an empty list when no items would be returned
  in that list, or not providing context manager interfaces on things
  that should logically have them.

  These wrappers are intended to compensate for these limitations and
  make it overall nicer for us to interact with libvirt.

  The API_VERSION constant provides version information about the
  underlying libvirt-python library as a virshx.common.VersionNumber
  instance.'''

from __future__ import annotations

import libvirt

from ..common import VersionNumber
from .exceptions import (NotConnected, EntityNotRunning, InvalidConfig, InvalidEntity, InsufficientPrivileges)
from .hypervisor import Hypervisor
from .domain import Domain
from .storage_pool import StoragePool
from .volume import Volume


def parse_libvirt_version(version: int) -> VersionNumber:
    '''Parse a libvirt version number into a version tuple.'''
    vstr = str(version)
    release = int(vstr[-3:].lstrip('0') or '0')
    minor = int(vstr[-6:-3].lstrip('0') or '0')
    major = int(vstr[:-6].lstrip('0'))
    return VersionNumber(major, minor, release)


API_VERSION = parse_libvirt_version(libvirt.getVersion())

__all__ = [
    'EntityNotRunning',
    'InsufficientPrivileges',
    'InvalidConfig',
    'InvalidEntity',
    'NotConnected',
    'Hypervisor',
    'Domain',
    'StoragePool',
    'Volume',
    'API_VERSION',
]
