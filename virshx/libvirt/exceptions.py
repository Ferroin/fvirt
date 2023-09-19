# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Exceptions used by virshx.libvirt classes.'''

from __future__ import annotations


class VirshxException(Exception):
    '''Base exception for all virshx exceptions.'''
    pass


class NotConnected(VirshxException):
    '''Raised when a hypervisor method is called without the hypervisor being connected.'''
    pass


class InvalidConfig(VirshxException):
    '''Raised when attempting to apply an invalid configuration.'''
    pass


class InvalidEntity(VirshxException):
    '''Raised when attempting to access an Entity that is no longer valid.'''
    pass


class EntityNotRunning(VirshxException):
    '''Raised when attempting runtime-only operations on an entity that is not running.'''
    pass


class InsufficientPrivileges(VirshxException):
    '''Raised when attempting to perform write operations on a read only connection.'''
    pass


class TimedOut(VirshxException):
    '''Raised when an operation with a timeout times out.'''
    pass


__all__ = [
    'VirshxException',
    'EntityNotRunning',
    'InsufficientPrivileges',
    'InvalidConfig',
    'InvalidEntity',
    'NotConnected',
    'TimedOut',
]
