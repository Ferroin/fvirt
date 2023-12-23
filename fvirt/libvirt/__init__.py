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
from .events import start_libvirt_event_thread
from .exceptions import (EntityNotRunning, EntityRunning, FeatureNotSupported, FVirtException, InsufficientPrivileges, InvalidConfig,
                         InvalidEntity, InvalidOperation, NotConnected, PlatformNotSupported, SubOperationFailed, TimedOut)
from .hypervisor import Hypervisor
from .storage_pool import StoragePool, StoragePoolState
from .stream import Stream, StreamError
from .uri import DRIVER_INFO, LIBVIRT_DEFAULT_URI, URI, Driver, Transport
from .volume import Volume
from ..version import VersionNumber

API_VERSION = VersionNumber.from_libvirt_version(libvirt.getVersion())

__all__ = [
    'API_VERSION',
    'Domain',
    'DomainState',
    'Driver',
    'DRIVER_INFO',
    'EntityNotRunning',
    'EntityRunning',
    'FeatureNotSupported',
    'FVirtException',
    'Hypervisor',
    'InsufficientPrivileges',
    'InvalidConfig',
    'InvalidEntity',
    'InvalidOperation',
    'LIBVIRT_DEFAULT_URI',
    'LifecycleResult',
    'NotConnected',
    'PlatformNotSupported',
    'start_libvirt_event_thread',
    'StoragePool',
    'StoragePoolState',
    'Stream',
    'StreamError',
    'SubOperationFailed',
    'TimedOut',
    'Transport',
    'URI',
    'Volume',
]
