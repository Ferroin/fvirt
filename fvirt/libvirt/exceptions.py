# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Exceptions used by fvirt.libvirt classes.'''

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar

import libvirt

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar('T')
W = TypeVar('W')


class FVirtException(Exception):
    '''Base exception for all fvirt exceptions.'''
    def __init__(self: Self, /, *args: Any, exc: type[Exception] | None = None, **kwargs: Any) -> None:
        self.underlying_exception = exc

        super().__init__(*args, **kwargs)


class PlatformNotSupported(FVirtException, NotImplementedError):
    '''Raised when attempting an fvirt operation which is not supported on this platform.'''


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


def call_libvirt(f: Callable[[], T], /) -> T:
    '''Call some code that may raise a libvirt exception, and handle it properly if one is raised.'''
    try:
        return f()
    except libvirt.libvirtError as e:
        match e.get_error_code():
            case (
                libvirt.VIR_ERR_OS_TYPE |
                libvirt.VIR_ERR_NO_KERNEL |
                libvirt.VIR_ERR_NO_OS |
                libvirt.VIR_ERR_NO_DEVICE |
                libvirt.VIR_ERR_XML_ERROR |
                libvirt.VIR_ERR_XML_DETAIL |
                libvirt.VIR_ERR_INVALID_MAC |
                libvirt.VIR_ERR_CONFIG_UNSUPPORTED
            ):
                e_cls: type[FVirtException] = InvalidConfig
            case (
                libvirt.VIR_ERR_INVALID_CONNECTION |
                libvirt.VIR_ERR_INVALID_DOMAIN |
                libvirt.VIR_ERR_INVALID_NETWORK |
                libvirt.VIR_ERR_INVALID_STORAGE_POOL |
                libvirt.VIR_ERR_INVALID_STORAGE_VOL |
                libvirt.VIR_ERR_INVALID_NODE_DEVICE |
                libvirt.VIR_ERR_INVALID_INTERFACE |
                libvirt.VIR_ERR_INVALID_NWFILTER |
                libvirt.VIR_ERR_INVALID_SECRET |
                libvirt.VIR_ERR_INVALID_DOMAIN_SNAPSHOT |
                libvirt.VIR_ERR_INVALID_STREAM
            ):
                e_cls = InvalidEntity
            case (
                libvirt.VIR_ERR_INVALID_OPERATION
            ):
                e_cls = InvalidOperation
            case _:
                e_cls = FVirtException

        raise e_cls(exc=e) from e


class libvirtCallWrapper(Generic[W]):
    '''Proxy class that adds automatic exception handling to method calls made against the wrapped object.'''
    __slots__ = (
        '__wrapped',
        '__callable_cache',
    )

    def __init__(self: Self, wrapped: W, /) -> None:
        self.__wrapped = wrapped
        self.__callable_cache: dict[str, Callable] = dict()

    def __getattr__(self: Self, v: str) -> Any:
        if v in self.__callable_cache:
            return self.__callable_cache[v]

        item = getattr(self.__wrapped, v)

        if callable(item):
            @wraps(item)
            def inner(*args: Any, **kwargs: Any) -> Any:
                return call_libvirt(lambda: item(*args, **kwargs))

            self.__callable_cache[v] = inner

            return inner

        return item
