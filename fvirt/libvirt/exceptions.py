# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Exceptions used by fvirt.libvirt classes.'''

from __future__ import annotations


class FVirtException(Exception):
    '''Base exception for all fvirt exceptions.'''
    pass


class NotConnected(FVirtException):
    '''Raised when a hypervisor method is called without the hypervisor being connected.'''
    pass


class InvalidConfig(FVirtException):
    '''Raised when attempting to apply an invalid configuration.'''
    pass


class InvalidEntity(FVirtException):
    '''Raised when attempting to access an Entity that is no longer valid.'''
    pass


class InvalidOperation(FVirtException):
    '''Raised when attempting an operation that is not valid on a particular entity.'''
    pass


class EntityNotRunning(InvalidOperation):
    '''Raised when attempting runtime-only operations on an entity that is not running.'''
    pass


class InsufficientPrivileges(FVirtException):
    '''Raised when attempting to perform write operations on a read only connection.'''
    pass


class TimedOut(FVirtException):
    '''Raised when an operation with a timeout times out.'''
    pass


__all__ = [
    'FVirtException',
    'EntityNotRunning',
    'InsufficientPrivileges',
    'InvalidConfig',
    'InvalidEntity',
    'InvalidOperation',
    'NotConnected',
    'TimedOut',
]
