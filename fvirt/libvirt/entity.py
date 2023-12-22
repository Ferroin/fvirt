# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Base class for libvirt object wrappers.'''

from __future__ import annotations

import enum
import logging

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Final, Literal, Self, TypeVar, cast, final
from uuid import UUID

from lxml import etree

from .descriptors import MethodProperty
from .exceptions import FeatureNotSupported, InsufficientPrivileges, InvalidEntity, NotConnected, libvirtCallWrapper
from .hypervisor import Hypervisor
from ..templates import get_environment

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pydantic import BaseModel

T = TypeVar('T')
LOGGER: Final = logging.getLogger(__name__)


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


class Entity(ABC):
    '''Abstract base class used by all fvirt libvirt object wrappers.

       This provides a handful of common functions, as well as some
       abstract properties that need to be defined by subclasses.

       Entity instances support the context manager protocol. Entering
       an entity’s context will ensure that the Hypervisor instance
       it is tied to is connected, and that the entity itself is valid.'''
    __slots__ = [
        '_entity',
        '_hv',
        '_parent',
        '_valid',
    ]

    def __init__(self: Self, entity: Any, parent: Hypervisor | Entity | None = None, /) -> None:
        match parent:
            case None:
                if not isinstance(entity, type(self)):
                    raise ValueError('Parent object or hypervisor must be specified when not passing an Entity.')
                else:
                    self._hv: Hypervisor = entity._hv
                    self._parent: Entity | None = entity._parent
                    self._entity: libvirtCallWrapper = entity._entity
            case Hypervisor():
                if not isinstance(entity, self._wrapped_class):
                    raise TypeError(f'Entity wrapped by {repr(type(self))} must be a {repr(self._wrapped_class)}.')

                self._hv = parent
                self._parent = None
                self._entity = libvirtCallWrapper(entity)
            case Entity():
                if not isinstance(entity, self._wrapped_class):
                    raise TypeError(f'Entity wrapped by {repr(type(self))} must be a {repr(self._wrapped_class)}.')

                self._hv = parent._hv
                self._parent = parent
                self._entity = libvirtCallWrapper(entity)
            case _:
                raise TypeError('Parent must be Hypervisor or Entity instance.')

        self._hv.open()
        self._valid = True

    def __del__(self: Self) -> None:
        self._hv.close()

    def __format__(self: Self, format_spec: str) -> str:
        fmt_args: dict[str, Any] = dict()

        for prop in self._format_properties:
            prop_value = getattr(self, prop, None)

            if prop_value is None:
                continue
            else:
                fmt_args[prop] = prop_value

        return format_spec.format(**fmt_args)

    def __eq__(self: Self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False

        if self._hv == other._hv and self._parent == other._parent:
            if self._entity == other._entity:
                return True

            return all({getattr(self, x) == getattr(other, x) for x in self._eq_properties})

        return False

    def __enter__(self: Self) -> Self:
        self._check_valid()
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

        if not self._hv.connected:
            raise NotConnected

    @property
    def _define_target(self: Self) -> Any:
        '''The object that will be used to define new instances of this entity.'''
        return self._hv

    @property
    @abstractmethod
    def _define_method(self: Self) -> str:
        '''Specify the name of the method to invoke to define a new
           instance of the Entity type.

           Children should override this appropriately.'''
        return ''

    @property
    def _config_flags(self: Self) -> int:
        '''Specify the flags that should be used when fetching configuration.

           Default implementation just returns 0.

           Children should override this if they need specific flags to
           be used when accessing config.'''
        return 0

    @property
    @abstractmethod
    def _wrapped_class(self: Self) -> type:
        '''Specifies what class the wrapped libvirt object is.

           This is used by the default __init__ method to do runtime
           type checking.

           Subclasses must override this method.'''
        return NotImplemented

    @property
    def _eq_properties(self: Self) -> set[str]:
        '''A set of properties that must be equal for two Entity instances to be considered equal.

           The default will work for most wrapped classes, but
           Entity types that lack a UUID or name should override this
           appropriately.'''
        return {'name', 'uuid'}

    @property
    def _format_properties(self: Self) -> set[str]:
        '''A set of properties usable with format().

           Any properties listed here can be used in a format specifier
           as named arguments when calling format() on an Entity
           instance. Child classes should override this to include any
           additional properties they want to be supported.'''
        return {'name', 'uuid'}

    @property
    def _mark_invalid_on_undefine(self: Self) -> bool:
        '''Whether or not the Entity should be marked invalid when undefined.'''
        return False

    @final
    @property
    def valid(self: Self) -> bool:
        '''Whether the Entity is valid or not.

           Defaults to True on instance creation.

           Will be set to false when something happens that causes the
           entity to become invalid (for example, destroying a transient
           domain).

           If this is false, calling most methods or accessing most
           properties will raise a fvirt.libvirt.InvalidEntity error.'''
        return self._valid

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

    @property
    def config_raw(self: Self) -> str:
        '''The raw XML configuration of the entity.

           Writing to this property will attempt to redefine the Entity
           with the specified config.

           For pre-parsed XML configuration, use the config property
           instead.'''
        self._check_valid()

        return cast(str, self._entity.XMLDesc(self._config_flags))

    @config_raw.setter
    def config_raw(self: Self, config: str) -> None:
        '''Recreate the entity with the specified raw XML configuration.'''
        if not self._define_method:
            raise ValueError('No method specified to redefine entity.')

        if self._hv.read_only:
            raise InsufficientPrivileges

        LOGGER.debug(f'Updating config for entity: {repr(self)}')

        define = getattr(self._define_target, self._define_method, None)

        if define is None:
            raise RuntimeError(f'Could not find define method { self._define_method } on target instance.')

        self._entity = define(config)._entity

        self._valid = True

    @property
    def config(self: Self) -> etree._ElementTree:
        '''The XML configuration of the Entity as an lxml.etree.Element instnce.

           Writing to this property will attempt to redefine the Entity
           with the specified config.

           For the raw XML as a string, use the rawConfig property.'''
        return etree.ElementTree(etree.fromstring(self.config_raw))

    @config.setter
    def config(self: Self, config: etree._Element | etree._ElementTree) -> None:
        '''Recreate the Entity with the specified XML configuration.'''
        self.config_raw = etree.tostring(config, encoding='unicode')

    def update_config_element(self: Self, /, path: str, text: str, *, reset_units: bool = False) -> bool:
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

        if self._hv.read_only:
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

    def update_config_attribute(self: Self, /, path: str, attrib: str, value: str) -> bool:
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

        if self._hv.read_only:
            raise InsufficientPrivileges

        config = self.config
        element = config.find(path)

        if not element:
            return False

        element.set(attrib, value)

        self.config = config
        return True

    def undefine(self: Self, /, *, idempotent: bool = True) -> LifecycleResult:
        '''Attempt to undefine the entity.

           If the entity is already undefined and idempotent is False
           (the default), return LifecycleResult.NO_OPERATION. If the
           entity is already undefined and idempotent is True, return
           LifecycleResult.SUCCESS.

           If the entity is not running, the Entity instance will become
           invalid and most methods and property access will raise a
           fvirt.libvirt.InvalidEntity exception.

           Returns LifecycleResult.SUCCESS if the operation succeeds, or
           raises an FVirtException if the operation fails.'''
        if not self.valid:
            if idempotent:
                return LifecycleResult.SUCCESS
            else:
                return LifecycleResult.NO_OPERATION

        mark_invalid = self._mark_invalid_on_undefine

        LOGGER.info(f'Undefining entity: {repr(self)}')
        self._entity.undefine()

        if mark_invalid:
            self._valid = False

        return LifecycleResult.SUCCESS

    def apply_xslt(self: Self, xslt: etree.XSLT, /) -> None:
        '''Apply the given etree.XSLT object to the domain's configuration.

           The XSLT document must specify an xsl:output element, and it
           must use a UTF-8 encoding for the output.

           This handles reading the config, applying the transformation,
           and then saving the config, all as one operation.'''
        self.config = xslt(self.config)

    @final
    @classmethod
    def _render_config(
        cls: type[Entity],
        /, *,
        template_name: str | None = None,
        template: str | None = None,
        **kwargs: Any
    ) -> str:
        '''Render a configuration for the entity type from a template.

           Either a template name or a raw template string must be specified.

           Any keyword arguments will be passed on to the template itself.

           If templating is not supported, a FeatureNotSupported error
           will be raised.'''
        env = get_environment()

        if env is None:
            raise FeatureNotSupported('Templating is not supported on this system.')

        if template is None:
            if template_name is None:
                raise ValueError('One of template or template_name must be specified.')

            tmpl = env.get_template(template_name)
        else:
            tmpl = env.from_string(template)

        return tmpl.render(**kwargs).lstrip().rstrip()

    @staticmethod
    def _get_template_info() -> tuple[type[BaseModel], str] | None:
        '''Provide parameters used for templating.

           If templating is not supported, this should return None.

           Otherwise, it should return a tuple of the model class for
           templating and the name of the template.

           Sub-classes that support templating should override this to
           provide the correct info. Sub-classes that do not support
           templating don’t need to do anything, as the default will
           unconditionally return None.'''
        return None

    @final
    @classmethod
    def new_config(
        cls: type[Entity],
        /, *,
        config: BaseModel | Mapping,
        template: str | None = None,
    ) -> Any:
        '''Generate a new configuration for this type of entity.'''
        template_info = cls._get_template_info()

        if template_info is None:
            raise FeatureNotSupported(f'{ cls.__name__ } does not support templating.')

        model, tmpl_name = template_info

        if config.__class__.__name__ != model.__name__:
            config = model.model_validate(config)

        return cls._render_config(
            template_name=tmpl_name,
            template=template,
            **config.model_dump(exclude_none=True),  # type: ignore
        )


class RunnableEntity(Entity):
    '''Base for entities that may be activated and inactivated.'''
    running: MethodProperty[bool] = MethodProperty(
        doc='Whether the entity is running or not.',
        type=bool,
        get='isActive',
    )
    persistent: MethodProperty[bool] = MethodProperty(
        doc='Whether the entity is running or not.',
        type=bool,
        get='isPersistent',
    )

    @property
    @abstractmethod
    def _config_flags_inactive(self: Self) -> int:
        '''Configuration flags to use when fetching persistent configuration.

           Must be overridden by child classes.'''
        return NotImplemented

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
    def config_raw(self: Self) -> str:
        '''The raw persistent XML configuration of the entity.

           If the entity is not persistent, this will return the current
           live configuration instead.

           If you just want the live configuration regardless, use the
           config_raw_live or config_live properties.

           Writing to this property will attempt to redefine the Entity
           with the specified config.

           For pre-parsed XML configuration, use the config property
           instead.'''
        self._check_valid()

        if self.persistent:
            try:
                return cast(str, self._entity.XMLDesc(self._config_flags_inactive))
            except Exception:
                return self.config_raw_live
        else:
            return self.config_raw_live

    @config_raw.setter
    def config_raw(self: Self, config: str) -> None:
        '''Recreate the entity with the specified raw XML configuration.'''
        if not self._define_method:
            raise ValueError('No method specified to redefine entity.')

        if self._hv.read_only:
            raise InsufficientPrivileges

        define = getattr(self._define_target, self._define_method, None)

        if define is None:
            raise RuntimeError(f'Could not find define method { self._define_method } on target instance.')

        self._entity = define(config)._entity

        self._valid = True

    @property
    def config_raw_live(self: Self) -> str:
        '''The raw live XML configuration of the entity.

           For pre-parsed configuration, use the config_live property instead.'''
        self._check_valid()

        return cast(str, self._entity.XMLDesc(self._config_flags))

    @property
    def config_live(self: Self) -> etree._ElementTree:
        '''The live XML configuration of the Entity as an lxml.etree.Element instnce.

           For the raw XML as a string, use the config_raw_live property.'''
        return etree.ElementTree(etree.fromstring(self.config_raw_live))

    @property
    def autostart(self: Self) -> bool | None:
        '''Whether or not the domain is configured to auto-start.

           A value of None wil be returned for entities that do not
           support this functionality.'''
        self._check_valid()

        if hasattr(self._entity, 'autostart'):
            return bool(self._entity.autostart())
        else:
            return None

    @autostart.setter
    def autostart(self: Self, value: bool) -> None:
        self._check_valid()

        if hasattr(self._entity, 'setAutostart'):
            if self._hv.read_only:
                raise InsufficientPrivileges

            LOGGER.info(f'Setting autostart state to {value} for entity: {repr(self)}')

            self._entity.setAutostart(int(value))
        else:
            raise AttributeError('Entity does not support autostart.')

    def start(self: Self, /, *, idempotent: bool = False) -> \
            Literal[LifecycleResult.SUCCESS, LifecycleResult.NO_OPERATION]:
        '''Attempt to start the entity.

           If called on an entity that is already running, do nothing and
           return LifecycleResult.SUCCESS or LifecycleResult.NO_OPERATION
           if the idempotent parameter is True or False respectively.

           If called on an entity that is not running, attempt to start
           it, and return LifecycleResult.SUCCESS if successful or
           raise an FVirtException if unsuccessful.'''
        self._check_valid()

        if self.running:
            if idempotent:
                return LifecycleResult.SUCCESS
            else:
                return LifecycleResult.NO_OPERATION

        LOGGER.info(f'Starting entity: {repr(self)}')
        self._entity.create()

        return LifecycleResult.SUCCESS

    def destroy(self: Self, /, *, idempotent: bool = False) -> \
            Literal[LifecycleResult.SUCCESS, LifecycleResult.NO_OPERATION]:
        '''Attempt to forcibly shut down the entity.

           If called on an entity that is not running, do nothing and
           return LifecycleResult.SUCCESS or LifecycleResult.NO_OPERATION
           if the idempotent parameter is True or False respectively.

           If the entity is running, attempt to forcibly shut it down,
           returning LifeCycleResult.SUCCESS on success or raising an
           FVirtException on a failure.

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

        LOGGER.info(f'Destroying entity: {repr(self)}')
        self._entity.destroy()

        if mark_invalid:
            self._valid = False

        return LifecycleResult.SUCCESS


__all__ = [
    'Entity',
    'LifecycleResult',
    'RunnableEntity',
]
