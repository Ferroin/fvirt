# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Custom descriptors for fvirt.libvirt.entity classes.'''

from __future__ import annotations

import warnings

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, cast, final

from lxml import etree

from ..util.units import unit_to_bytes

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from .entity import ConfigurableEntity

T = TypeVar('T')


class ReadDescriptor(Generic[T], ABC):
    '''Abstract base class for read descriptors.

       This handles type conversion and fallback logic, as well as
       validity checking when attached to an Entity object.'''
    def __init__(
        self: Self,
        /, *,
        doc: str,
        type: Callable[[Any], T],
        fallback: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._type = type
        self._fallback = fallback
        self.__doc__ = doc

    @final
    def __get__(self: Self, instance: Any, _owner: Any) -> T:
        if instance is None:
            return self  # type: ignore

        if hasattr(instance, '_check_valid'):
            instance._check_valid()

        try:
            v = self._get_value(instance)
        except AttributeError:
            if self._fallback is not None:
                fb = getattr(instance, self._fallback, None)

                if fb is None:
                    raise AttributeError(f'{ repr(instance) }:{ repr(self) }')
                else:
                    return self._type(fb)
            else:
                raise AttributeError(f'{ repr(instance) }:{ repr(self) }')

        return self._type(v)

    @abstractmethod
    def _get_value(self: Self, instance: Any) -> Any:
        '''Used to retrieve the value for the descriptor.

           If the value cannot be found, this should raise an
           AttributeError, which will trigger the fallback logic in the
           __get__ method.'''


class WriteDescriptor(Generic[T]):
    '''Abstract base class for writable descriptors.

       This handles input validation logic, as well as validity checking
       when attached to an entity object.

       This must be used alongside the ReadDescriptor class to have
       working docstrings.

       The validator function should take the value to write and the
       object instance that the descriptor is being called for, and
       raise an appropriate exception (usually a TypeError or ValueError)
       if validation fails.'''
    def __init__(
        self: Self,
        /, *,
        validator: Callable[[T, Any], None],
        **kwargs: Any,
    ) -> None:
        self._validator = validator

    @final
    def __set__(self: Self, instance: Any, value: T) -> None:
        if hasattr(instance, '_check_valid'):
            instance._check_valid()

        self._validator(value, instance)
        self._set_value(value, instance)

    @abstractmethod
    def _set_value(self: Self, value: T, instance: Any) -> None:
        '''Used to set the value for the descriptor.

           If the value cannot be set,t his should raise an appropriate
           error (usually an AttributeError).'''


class MethodProperty(ReadDescriptor[T]):
    '''A descriptor that indirects reads to a method call on a property of the object it is attached to.'''
    def __init__(
        self: Self,
        /, *,
        doc: str,
        get: str,
        type: Callable[[Any], T],
        target: str = '_entity',
        extra_get_args: Sequence[Any] = [],
        fallback: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._target = target
        self._get = get
        self._get_args = extra_get_args

        super().__init__(doc=doc, type=type, fallback=fallback, **kwargs)

    def __repr__(self: Self) -> str:
        return f'<MethodProperty: target={ self._target }, get={ self._get }, fallback={ self._fallback }>'

    def _get_value(self: Self, instance: Any) -> Any:
        t = getattr(instance, self._target, None)

        if t is not None:
            c = getattr(t, self._get)

            if c is not None:
                return c(*self._get_args)
            else:
                warnings.warn(f'{ repr(instance) }:{ repr(self) }: Failed to load target method.', RuntimeWarning, stacklevel=2)
        else:
            warnings.warn(f'{ repr(instance) }:{ repr(self) }: Failed to load target property.', RuntimeWarning, stacklevel=2)

        raise AttributeError(f'{ repr(instance) }:{ repr(self) }')


class SettableMethodProperty(MethodProperty[T], WriteDescriptor[T]):
    '''A descriptor that indirects reads and writes to method calls on a property of the object it is attached to.'''
    def __init__(
        self: Self,
        /, *,
        doc: str,
        get: str,
        set: str,
        target: str = '_entity',
        type: Callable[[Any], T] = lambda x: cast(T, x),
        validator: Callable[[T, Any], None] = lambda x, y: None,
        extra_get_args: Sequence[Any] = [],
        extra_set_args: Sequence[Any] = [],
        fallback: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._set = set
        self._set_args = extra_set_args

        super().__init__(
            doc=doc,
            target=target,
            get=get,
            type=type,
            extra_get_args=extra_get_args,
            fallback=fallback,
            validator=validator,
            **kwargs,
        )

    def __repr__(self: Self) -> str:
        return f'<SettableMethodProperty: target={ self._target }, get={ self._get }, set={ self._set }, fallback={ self._fallback }>'

    def __set_value(self: Self, value: T, instance: Any) -> None:
        t = getattr(instance, self._target, None)

        if t is not None:
            c = getattr(t, self._set, None)

            if c is not None:
                c(t, value, *self._set_args)
            else:
                raise AttributeError(f'{ repr(instance) }:{ repr(self) }')
        else:
            raise AttributeError(f'{ repr(instance) }:{ repr(self) }')


class ConfigProperty(ReadDescriptor[T]):
    '''A descriptor that maps a config value in a ConfigurableEntity to a property.

       For writable configuration properties, use ConfigElementProperty
       or ConfigAttributeProperty instead.'''
    def __init__(
        self: Self,
        /, *,
        doc: str,
        path: str,
        type: Callable[[Any], T] = lambda x: cast(T, x),
        units_to_bytes: bool = False,
        fallback: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._path = path
        self._xpath = etree.XPath(path, smart_strings=False)
        self._units_to_bytes = units_to_bytes

        super().__init__(doc=doc, type=type, fallback=fallback, **kwargs)

    def __repr__(self: Self) -> str:
        return f'<ConfigProperty: path={ self._path }, fallback={ self._fallback }>'

    def _get_value(self: Self, instance: ConfigurableEntity) -> Any:
        ret: Any = None
        result = self._xpath(instance.config)

        if result is None or result == []:
            raise AttributeError(f'{ repr(instance) }:{ repr(self) }')

        if isinstance(result, list):
            e: Any = result[0]
        else:
            e = result

        if isinstance(e, bool) or isinstance(e, str) or isinstance(e, float) or isinstance(e, bytes) or isinstance(e, tuple):
            ret = e
        elif self._units_to_bytes:
            unit = e.get('unit', default='bytes')
            value = int(str(e.text))

            ret = unit_to_bytes(value, unit)
        else:
            ret = e.text

        return ret


class ConfigElementProperty(ConfigProperty[T], WriteDescriptor[T]):
    '''A descriptor that indirects reads and writes to an element in the object configuration.'''
    def __init__(
        self: Self,
        /, *,
        doc: str,
        path: str,
        type: Callable[[Any], T] = lambda x: cast(T, x),
        units_to_bytes: bool = False,
        fallback: str | None = None,
        validator: Callable[[T, Any], None] = lambda x, y: None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            doc=doc,
            path=path,
            type=type,
            units_to_bytes=units_to_bytes,
            fallback=fallback,
            validator=validator,
            **kwargs,
        )

    def __repr__(self: Self) -> str:
        return f'<ConfigElementProperty: path={ self._path }, fallback={ self._fallback }>'

    def _set_value(self: Self, value: T, instance: Any) -> None:
        instance.updateConfigElement(self._path, str(value), reset_units=self._units_to_bytes)


class ConfigAttributeProperty(ReadDescriptor[T], WriteDescriptor[T]):
    '''A descriptor that indirects reads and writes to an attrihbute on an element in the object configuration.'''
    def __init__(
        self: Self,
        /, *,
        doc: str,
        path: str,
        attr: str,
        type: Callable[[Any], T] = lambda x: cast(T, x),
        fallback: str | None = None,
        validator: Callable[[T, Any], None] = lambda x, y: None,
        **kwargs: Any,
    ) -> None:
        self._path = path
        self._attr = attr

        super().__init__(
            doc=doc,
            type=type,
            fallback=fallback,
            validator=validator,
            **kwargs,
        )

    def __repr__(self: Self) -> str:
        return f'<ConfigAttributeProperty: path={ self._path }, attr={ self._attr }, fallback={ self._fallback }>'

    def _get_value(self: Self, instance: Any) -> Any:
        e = instance.config.find(self._path)

        if e is None:
            return None

        return e.get(self._attr, default=None)

    def _set_value(self: Self, value: T, instance: Any) -> None:
        instance.updateConfigAttribute(self._path, self._attr, str(value))
