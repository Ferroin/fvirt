# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Exceptions used by fvirt.libvirt classes.'''

from __future__ import annotations


class FVirtException(Exception):
    '''Base exception for all fvirt exceptions.'''


class PlatformNotSupported(FVirtException, NotImplementedError):
    '''Raised when attempting an operation which is not supported on this platform.'''


class FeatureNotSupported(FVirtException, RuntimeError):
    '''Raised when attempting to use an optional fvirt feature which is not supported on this system.'''


class NotConnected(FVirtException):
    '''Raised when a hypervisor method is called without the hypervisor being connected.'''


class InvalidConfig(FVirtException):
    '''Raised when attempting to apply an invalid configuration.'''


class InvalidEntity(FVirtException):
    '''Raised when attempting to access an Entity that is no longer valid.'''


class InvalidOperation(FVirtException):
    '''Raised when attempting an operation that is not valid on a particular entity.'''


class EntityNotRunning(InvalidOperation):
    '''Raised when attempting runtime-only operations on an entity that is not running.'''


class EntityRunning(InvalidOperation):
    '''Raised when attempting an operation that requires an entity to not be running on a running entity.'''


class InsufficientPrivileges(FVirtException, PermissionError):
    '''Raised when attempting to perform write operations on a read only connection.'''


class TimedOut(FVirtException, TimeoutError):
    '''Raised when an operation with a timeout times out.'''


class SubOperationFailed(FVirtException):
    '''Raised when an operation being performed as part of another operation fails.'''


__all__ = [
    'FVirtException',
    'PlatformNotSupported',
    'FeatureNotSupported',
    'EntityNotRunning',
    'EntityRunning',
    'InsufficientPrivileges',
    'InvalidConfig',
    'InvalidEntity',
    'InvalidOperation',
    'NotConnected',
    'TimedOut',
    'SubOperationFailed',
]
