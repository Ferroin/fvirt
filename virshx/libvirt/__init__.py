# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Wrapper classes for libvit.

  The official libvirt bindings for Python are essentially a 1:1 mapping
  of the C API. This leads to a lot of questionable behaviors such as
  returning None instead of an empty list when no items would be returned
  in that list, or not providing context manager interfaces on things
  that should logically have them.

  These wrappers are intended to compensate for these limitations and
  make it overall nicer for us to interact with libvirt.'''

from __future__ import annotations

from .domain import Domain
from .exceptions import (NotConnected, InvalidConfig, InvalidDomain, InsufficientPrivileges)
from .hypervisor import Hypervisor

__all__ = [
    'Domain',
    'NotConnected',
    'InvalidConfig',
    'InvalidDomain',
    'InsufficientPrivileges',
    'Hypervisor',
]
