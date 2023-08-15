# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Exceptions used by virshx.libvirt classes.'''

from __future__ import annotations

from ..common import VirshxException


class NotConnected(VirshxException):
    '''Raised when a hypervisor method is called without the hypervisor being connected.'''
    pass


class InvalidConfig(VirshxException):
    '''Raised when attempting to apply an invalid configuration.'''
    pass


class InvalidDomain(VirshxException):
    '''Raised when attempting to access a domain that is no longer valid.'''
    pass


class InsufficientPrivileges(VirshxException):
    '''Raised when attempting to perform write operations on a read only connection.'''
    pass


__all__ = [
    'NotConnected',
    'InvalidConfig',
    'InvalidDomain',
    'InsufficientPrivileges',
]
