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
  underlying libvirt-python library as a fvirt.version.VersionNumber
  instance.'''

from __future__ import annotations

import libvirt

from .domain import Domain, DomainState
from .entity import LifecycleResult
from .exceptions import EntityNotRunning, InsufficientPrivileges, InvalidConfig, InvalidEntity, InvalidOperation, NotConnected
from .hypervisor import Hypervisor
from .storage_pool import StoragePool
from .uri import CLIENT_ONLY_DRIVERS, LIBVIRT_DEFAULT_URI, SESSION_DRIVERS, SYSTEM_DRIVERS, URI, Driver, Transport
from .volume import Volume
from ..version import VersionNumber

API_VERSION = VersionNumber.from_libvirt_version(libvirt.getVersion())

__all__ = [
    'EntityNotRunning',
    'InsufficientPrivileges',
    'InvalidConfig',
    'InvalidEntity',
    'InvalidOperation',
    'NotConnected',
    'LifecycleResult',
    'Hypervisor',
    'Domain',
    'DomainState',
    'StoragePool',
    'URI',
    'Driver',
    'Transport',
    'SESSION_DRIVERS',
    'SYSTEM_DRIVERS',
    'CLIENT_ONLY_DRIVERS',
    'LIBVIRT_DEFAULT_URI',
    'Volume',
    'API_VERSION',
]
