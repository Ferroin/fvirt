# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Base class for libvirt object wrappers.'''

from __future__ import annotations

import enum

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self, Generic, TypeVar, Literal, cast
from uuid import UUID

import libvirt

from lxml import etree

from ..util.units import unit_to_bytes
from .exceptions import InvalidEntity, InsufficientPrivileges, NotConnected

if TYPE_CHECKING:
    from collections.abc import Callable

    from .hypervisor import Hypervisor

T = TypeVar('T')


class Entity(ABC):
    '''ABC used by all fvirt libvirt object wrappers.

       This provides a handful of common functions, as well as some
       abstract properties that need to be defined by subclasses.

       Entities support the context manager protocol. Entering an
       entity’s context will ensure that the Hypervisor instance it
       is tied to is connected, and that the entity itself is valid.'''
    __slots__ = [
        '__conn',
        '__parent',
        '__entity',
        '__valid',
    ]

    def __init__(self: Self, entity: Any, parent: Hypervisor | Entity) -> None:
        if isinstance(parent, Entity):
            self.__conn = parent._hv
            self.__parent: Entity | None = parent
        else:
            self.__conn = parent
            self.__parent = None

        self.__entity = entity
        self.__valid = True

    def __format__(self: Self, format_spec: str) -> str:
        fmt_args: dict[str, Any] = dict()

        for prop in self._format_properties:
            prop_value = getattr(self, prop, None)

            if prop_value is None:
                continue
            elif hasattr(prop_value, '__get__'):
                fmt_args[prop] = prop_value.__get__(self)
            else:
                fmt_args[prop] = prop_value

        return format_spec.format(**fmt_args)

    def __enter__(self: Self) -> Self:
        self._check_valid()

        if self.__conn._connection is None:
            raise NotConnected

        return self

    def __exit__(self: Self, *args: Any, **kwargs: Any) -> None:
        pass

    def _check_valid(self: Self) -> None:
        '''Check that the instance is still valid.

           Child classes should call this method at the start of any
           function that should not be run on invalid instances. It
           will handle raising the correct error if the instance is
           not valid.'''
        if not self.valid:
            raise InvalidEntity

    @property
    def _format_properties(self: Self) -> set[str]:
        '''A list of properties usable with format().

           Any properties listed here can be used in a format
           specifier as named arguments when calling format() on an
           Entity instance. Child classes should override this to any
           additional properties they want to be supported.'''
        return {'name', 'uuid'}

    @property
    def _mark_invalid_on_undefine(self: Self) -> bool:
        '''Whether or not the Entity should be marked invalid when undefined.'''
        return False

    @property
    def _entity(self: Self) -> Any:
        '''The underlying libvirt object that this class is wrapping.

           This is provided so that users can work around our bindings
           not providing some function they need, but it’s usage is
           generally discouraged as calling certain methods will cause
           the encapsulating Entity instance to stop working correctly.'''
        return self.__entity

    @property
    def _hv(self: Self) -> Hypervisor:
        '''The hypervisor instance this entity is tied to.

           API users should generally not need to access this at all.'''
        return self.__conn

    @property
    def valid(self: Self) -> bool:
        '''Whether the Entity is valid or not.

           Defaults to True on instance creation.

           Will be set to false when something happens that causes the
           entity to become invalid (for example, destroying a transient
           domain).

           If this is false, calling most methods or accessing most
           properties will raise a fvirt.libvirt.InvalidEntity error.'''
        return self.__valid

    @property
    def name(self: Self) -> str:
        '''The name of the entity.'''
        self._check_valid()

        return cast(str, self._entity.name())

    @property
    def uuid(self: Self) -> UUID | None:
        '''The UUID of the entity, or None if it has no UUID.'''
        self._check_valid()

        get_uuid = getattr(self._entity, 'UUIDString')

        if get_uuid is None:
            return None

        return UUID(get_uuid())


class LifecycleResult(enum.Enum):
    '''An enumeration indicating the result of an entity lifecycle operation.

       SUCCESS indicates a successful operation.

       FAILURE indicates a failed operation.

       NO_OPERATION indicates that nothing was done because the Entity
       is already in the requested state.

       TIMED_OUT indicates that a timeout on the operation was exceeded.

       FORCED indicates that the state transition was forced due to
       initially failing.'''
    SUCCESS = enum.auto()
    FAILURE = enum.auto()
    NO_OPERATION = enum.auto()
    TIMED_OUT = enum.auto()
    FORCED = enum.auto()


class ConfigurableEntity(Entity):
    '''ABC used for configurable Entities.'''
    @property
    def _define_target(self: Self) -> Any:
        '''The object that will be used to define new instances of this entity.'''
        return self.__conn

    @property
    @abstractmethod
    def _define_method(self: Self) -> str:
        '''Specify the name of the method to invoke to define a new
           instance of the Entity type.

           Children should override this appropriately.'''
        return ''

    @property
    @abstractmethod
    def _config_flags(self: Self) -> int:
        '''Specify the flags that should be used when fetching configuration.

           Default implementation just returns 0.

           Children should override this if they need specific flags to
           be used when accessing config.'''
        return 0

    @property
    def configRaw(self: Self) -> str:
        '''The raw XML configuration of the entity.

           Writing to this property will attempt to redefine the Entity
           with the specified config.

           For pre-parsed XML configuration, use the config property
           instead.'''
        self._check_valid()

        return cast(str, self._entity.XMLDesc(self._config_flags))

    @configRaw.setter
    def configRaw(self: Self, config: str) -> None:
        '''Recreate the entity with the specified raw XML configuration.'''
        if not self._define_method:
            raise ValueError('No method specified to redefine entity.')

        if self.__conn.read_only:
            raise InsufficientPrivileges

        define = getattr(self._define_target, self._define_method, None)

        if define is None:
            raise RuntimeError(f'Could not find define method { self._define_method } on target instance.')

        self.__entity = define(config).__entity

        self.__valid = True

    @property
    def config(self: Self) -> etree._Element:
        '''The XML configuration of the Entity as an lxml.etree.Element instnce.

           Writing to this property will attempt to redefine the Entity
           with the specified config.

           For the raw XML as a string, use the rawConfig property.'''
        return etree.fromstring(self.configRaw)

    @config.setter
    def config(self: Self, config: etree._Element) -> None:
        '''Recreate the Entity with the specified XML configuration.'''
        self.configRaw = etree.tostring(config, encoding='unicode')

    @property
    def name(self: Self) -> str:
        '''The name of the entity.'''
        return super().name

    @name.setter
    def name(self: Self, name: str) -> None:
        if not isinstance(name, str):
            raise ValueError('Name must be a string.')

        self._check_valid()

        if self.__conn.read_only:
            raise InsufficientPrivileges

        self.updateConfigElement('./name', name)

    def updateConfigElement(self: Self, path: str, text: str, *, reset_units: bool = False) -> bool:
        '''Update the element at path in config to have a value of text.

           `path` should be a valid XPath expression that evaluates to
           a single element.

           If `reset_units` is true, also set an attribute named `units`
           on the target element to a value of `bytes`.

           Returns True if the path matched or False if it did not.

           If updating the config fails for a reason other than not
           matching the path, an error will be raised.'''
        if not isinstance(text, str):
            raise ValueError('text must be a string.')

        self._check_valid()

        if self.__conn.read_only:
            raise InsufficientPrivileges

        config = self.config
        element = config.find(path)

        if not element:
            return False

        element.text = text

        if reset_units:
            element.set('units', 'bytes')

        self.config = config
        return True

    def updateConfigAttribute(self: Self, path: str, attrib: str, value: str) -> bool:
        '''Update the attribute attrib of element at path in config to have a value of value.

           `path` should be a valid XPath expression that evaluates to
           a single element.

           `attrib` should be the name of an attribute on that element
           to update the value of.

           Returns True if the path matched or False if it did not.

           If updating the config fails for a reason other than not
           matching the path, an error will be raised.'''
        if not isinstance(value, str):
            raise ValueError('value must be a string.')

        self._check_valid()

        if self.__conn.read_only:
            raise InsufficientPrivileges

        config = self.config
        element = config.find(path)

        if not element:
            return False

        element.set(attrib, value)

        self.config = config
        return True

    def undefine(self: Self, /, *, idempotent: bool = False) -> \
            Literal[LifecycleResult.SUCCESS, LifecycleResult.FAILURE, LifecycleResult.NO_OPERATION]:
        '''Attempt to undefine the entity.

           If the entity is already undefined and idempotent is False
           (the default), return LifecycleResult.NO_OPERATION. If the
           entity is already undefined and idempotent is True, return
           LifecycleResult.SUCCESS.

           If the entity is not running, the Entity instance will become
           invalid and most methods and property access will raise a
           fvirt.libvirt.InvalidEntity exception.

           Returns LifecycleResult.SUCCESS if the operation succeeds, or
           LifecycleResult.FAILURE if it fails due to a libvirt error.'''
        if not self.valid:
            return LifecycleResult.NO_OPERATION

        try:
            self._entity.undefine()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        if self._mark_invalid_on_undefine:
            self.__valid = False

        return LifecycleResult.SUCCESS

    def applyXSLT(self: Self, xslt: etree.XSLT) -> None:
        '''Apply the given etree.XSLT object to the domain's configuration.

           The XSLT document must specify an xsl:output element, and it
           must use a UTF-8 encoding for the output.

           This handles reading the config, applying the transformation,
           and then saving the config, all as one operation.'''
        self.configRaw = str(xslt(self.config))


class ConfigProperty(Generic[T]):
    '''A descriptor for accessing items in the configuration of a ConfigurableEntity.

       The path argument is an XPath expression that when evaluated
       against the config produces the value of the property.

       The typ argument is a function used to ensure the returned value
       is the right type.

       THe units_to_bytes argument is a boolean which if True, enables
       automatic conversion of libvirt-style numbers with units down to
       integral bytes. If this is True, the path argument must evaluate to
       an element with a numerical value for it’s text and an optional
       attribute named units which specifies the units of the value.

       The fallback argument is either the name of a different attribute
       on the instance to use as a default value, or None if we should
       raise an attribute error when we can't find a value.

       For writable configuration properties, use ConfigElementProperty
       or ConfigAttributeProperty instead.'''
    def __init__(
            self: Self,
            /,
            path: str,
            *,
            typ: Callable[[Any], T] | None = None,
            units_to_bytes: bool = False,
            fallback: str | None = None,
            ) -> None:
        self._path = path
        self._xpath = etree.XPath(path, smart_strings=False)
        self._type = typ
        self._units_to_bytes = units_to_bytes
        self._fallback = fallback

    def __get__(self: Self, instance: ConfigurableEntity, _owner: Any) -> T:
        ret: Any = None

        if self._units_to_bytes:
            e = instance.config.find(self._path)

            if e is None:
                if self._fallback is not None:
                    fb = getattr(instance, self._fallback, None)

                    if fb is None:
                        raise AttributeError
                    elif hasattr(fb, '__get__'):
                        ret = fb.__get__(instance)
                    else:
                        ret = fb
                else:
                    raise AttributeError
            else:
                unit = str(e.get('unit', default='bytes'))
                value = int(str(e.text))

                ret = unit_to_bytes(value, unit)
        else:
            ret = self._xpath(instance.config)

            if ret is None or ret == []:
                raise AttributeError
            elif isinstance(ret, list):
                ret = ret[0]

        if self._type is not None:
            return self._type(ret)
        else:
            return cast(T, ret)

    def __set__(self: Self, instance: ConfigurableEntity, _value: T) -> None:
        raise AttributeError(f'Unable to set config property at { self._path } for instance { instance }.')


class ConfigElementProperty(ConfigProperty, Generic[T]):
    '''A writable descriptor for accessing the value of an element in the configuration of a ConfigurableEntity.

       The `path` argument specifies the path to the element.

       `typ` and `units_to_bytes` have the same meaning as for ConfigProperty.

       The validator argument is an optional function which will be
       called when trying to set the property to verify that the value
       is acceptable for that instance. It should raise an error if the
       value is not acceptable.'''
    def __init__(
            self: Self,
            /,
            path: str,
            *,
            typ: Callable[[Any], T] | None = None,
            units_to_bytes: bool = False,
            fallback: str | None = None,
            validator: Callable[[T, Any], None] | None = None,
            ) -> None:
        self._validator = validator
        super().__init__(path=path, typ=typ, units_to_bytes=units_to_bytes, fallback=fallback)

    def __set__(self: Self, instance: ConfigurableEntity, value: T) -> None:
        if self._validator is not None:
            self._validator(value, instance)

        instance.updateConfigElement(self._path, str(value), reset_units=self._units_to_bytes)


class ConfigAttributeProperty(ConfigProperty, Generic[T]):
    '''A writable descriptor for accessing the value of an attribute of an element in the configuration of a ConfigurableEntity.

       The `path` argument specifies the path to the element the desired
       attribute is part of.

       The `attrib` arugment specifies the name of the attribute.

       `typ` has the same meaning as for ConfigProperty.

       The validator argument is an optional function which will be
       called when trying to set the property to verify that the value
       is acceptable for that instance. It should raise an error if the
       value is not acceptable.'''
    def __init__(
            self: Self,
            /,
            path: str,
            attrib: str,
            *,
            typ: Callable[[Any], T] | None = None,
            fallback: str | None = None,
            validator: Callable[[T, Any], None] | None = None,
            ) -> None:
        self._validator = validator
        self._attrib = attrib
        super().__init__(path=path, typ=typ, units_to_bytes=False, fallback=fallback)

    def __get__(self: Self, instance: ConfigurableEntity, _owner: Any) -> T | None:
        e = instance.config.find(self._path)

        if e is None:
            return None

        ret = e.get(self._attrib, default=None)

        if ret is None:
            return None
        elif self._type is not None:
            return cast(T, self._type(ret))
        else:
            return cast(T, ret)

    def __set__(self: Self, instance: ConfigurableEntity, value: T) -> None:
        if self._validator is not None:
            self._validator(value, instance)

        instance.updateConfigAttribute(self._path, self._attrib, str(value))


class RunnableEntity(Entity):
    '''ABC for entities that may be activated and inactivated.'''
    @property
    def _format_properties(self: Self) -> set[str]:
        return super()._format_properties | {
            'running',
            'persistent',
        }

    @property
    def _mark_invalid_on_undefine(self: Self) -> bool:
        return not self.running

    @property
    def running(self: Self) -> bool:
        '''Whether the entity is active or not.'''
        if not self.valid:
            return False

        return bool(self._entity.isActive())

    @property
    def persistent(self: Self) -> bool:
        '''Whether the entity is persistent or not.'''
        if not self.valid:
            return False

        return bool(self._entity.isPersistent())

    def start(self: Self, /, *, idempotent: bool = False) -> \
            Literal[LifecycleResult.SUCCESS, LifecycleResult.FAILURE, LifecycleResult.NO_OPERATION]:
        '''Attempt to start the entity.

           If called on an entity that is already running, do nothing and
           return LifecycleResult.SUCCESS or LifecycleResult.NO_OPERATION
           if the idempotent parameter is True or False respectively.

           If called on an entity that is not running, attempt to start
           it, and return LifecycleResult.SUCCESS if successful or
           LifecycleResult.FAILUREif unsuccessful.'''
        self._check_valid()

        if self.running:
            if idempotent:
                return LifecycleResult.SUCCESS
            else:
                return LifecycleResult.NO_OPERATION

        try:
            self._entity.create()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        return LifecycleResult.SUCCESS

    def destroy(self: Self, /, *, idempotent: bool = False) -> \
            Literal[LifecycleResult.SUCCESS, LifecycleResult.FAILURE, LifecycleResult.NO_OPERATION]:
        '''Attempt to forcibly shut down the entity.

           If the entity is not running, do nothing and return the value
           of the idempotent parameter.

           If the entity is running, attempt to forcibly shut it down,
           returning True on success or False on failure.

           If the entity is transient, the Entity instance will become
           invalid and most methods and property access will raise a
           fvirt.libvirt.InvalidEntity exception.'''
        if not self.running or not self.valid:
            if idempotent:
                return LifecycleResult.SUCCESS
            else:
                return LifecycleResult.NO_OPERATION

        mark_invalid = False

        if not self.persistent:
            mark_invalid = True

        try:
            self._entity.destroy()
        except libvirt.libvirtError:
            return LifecycleResult.FAILURE

        if mark_invalid:
            self._valid = False

        return LifecycleResult.SUCCESS


__all__ = [
    'Entity',
    'LifecycleResult',
    'ConfigurableEntity',
    'ConfigProperty',
    'ConfigElementProperty',
    'ConfigAttributeProperty',
    'RunnableEntity',
]
