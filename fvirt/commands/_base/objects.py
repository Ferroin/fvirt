# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command mixins for handling various object types.'''

from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, Self, Type, TypeGuard, cast

import click

from .exitcode import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from ...libvirt import Hypervisor
    from ...libvirt.entity import Entity
    from ...util.match import MatchArgument

LOGGER: Final = logging.getLogger(__name__)


def is_object_mixin(obj: Any) -> TypeGuard[ObjectMixin]:
    '''Indicate that a given object is an ObjectMixin.

       Commands that use ObjectMixin functionality should assert this
       in their __init__ method.'''
    if not hasattr(obj, '_OBJ_MIXIN'):
        raise RuntimeError

    return True


@dataclass(kw_only=True, slots=True)
class DisplayProperty:
    '''Defines a property of an object that can be displayed by the CLI.'''
    name: str
    title: str
    prop: str
    use_units: bool = False
    right_align: bool = False
    color: Callable[[Any], str] = lambda x: str(x)


class ObjectMixin(ABC):
    '''Abstract base class for object mixins.'''
    @property
    def _OBJ_MIXIN(self: Self) -> bool:
        '''Marks the class as using an object mixin.'''
        return True

    @property
    def HAS_PARENT(self: Self) -> bool:
        '''Indicates if the object mixin uses a parent.'''
        parent_props = {
            self.PARENT_ATTR,
            self.PARENT_METAVAR,
            self.PARENT_NAME,
        }

        if None in parent_props and parent_props != {None}:
            raise RuntimeError

        return parent_props != {None}

    @property
    @abstractmethod
    def NAME(self: Self) -> str:
        '''The name of the entity type.'''
        return NotImplemented

    @property
    @abstractmethod
    def CLASS(self: Self) -> Type[Entity]:
        '''The class used to represent the object.'''
        return NotImplemented

    @property
    @abstractmethod
    def METAVAR(self: Self) -> str:
        '''The metavar to use in help output for arguments that specify the entity.'''
        return NotImplemented

    @property
    @abstractmethod
    def LOOKUP_ATTR(self: Self) -> str:
        '''Specifies the name of the EntityAccess attribute needed for a lookup.'''
        return NotImplemented

    @property
    @abstractmethod
    def DEFINE_METHOD(self: Self) -> str:
        '''Sepcifies the name of the method used to define the entity.'''
        return NotImplemented

    @property
    def CREATE_METHOD(self: Self) -> str | None:
        '''Sepcifies the name of the method used to create the entity.'''
        return None  # pragma: no cover

    @property
    @abstractmethod
    def DISPLAY_PROPS(self: Self) -> Mapping[str, DisplayProperty]:
        '''Specifies the display properties for the entity.'''
        return NotImplemented

    @property
    def DEFAULT_COLUMNS(self: Self) -> Sequence[str]:
        '''Specifies the default display properties for a list view.'''
        return list(self.DISPLAY_PROPS.keys())

    @property
    def SINGLE_LIST_PROPS(self: Self) -> set[str]:
        '''Specifies the display properties available for a single list view.'''
        return {x for x in self.DISPLAY_PROPS.keys() if x in {'name', 'uuid', 'id', 'key'}}

    @property
    def PARENT_ATTR(self: Self) -> str | None:
        '''Specifies the name of the EntityAccess attribute needed to look up a parent.'''
        return None  # pragma: no cover

    @property
    def PARENT_NAME(self: Self) -> str | None:
        '''The name of the parent entity, used in documentation.'''
        return None  # pragma: no cover

    @property
    def PARENT_METAVAR(self: Self) -> str | None:
        '''The metavar to use in help output for arguments that specify the parent entity.'''
        return None  # pragma: no cover

    def mixin_params(self: Self, required: bool = False) -> tuple[click.Parameter, ...]:
        '''Return a tuple of arguments for specifying the entity and possibly the parent.'''
        entity_arg = click.Argument(
            param_decls=('entity',),
            nargs=1,
            metavar=self.METAVAR,
            required=required,
        )

        if self.PARENT_METAVAR is not None:
            return self.mixin_parent_params() + (entity_arg,)
        else:
            return (entity_arg,)

    def mixin_parent_params(self: Self) -> tuple[click.Parameter, ...]:
        '''Return a tuple of arguments for specifying the parent.'''
        return (click.Argument(
            param_decls=('parent',),
            nargs=1,
            metavar=self.PARENT_METAVAR,
            required=True
        ),)

    def get_entity(self: Self, ctx: click.Context, parent: Entity | Hypervisor, ident: Any) -> Entity:
        '''Look up an entity based on an identifier.'''
        from ...libvirt.entity import Entity
        from ...libvirt.entity_access import EntityAccess

        entity = cast(EntityAccess[Entity], getattr(parent, self.LOOKUP_ATTR)).get(ident)

        if entity is None:
            LOGGER.error(f'Could not find { self.NAME } "{ ident }"')
            ctx.exit(ExitCode.ENTITY_NOT_FOUND)

        return entity

    def get_parent_obj(self: Self, ctx: click.Context, hv: Hypervisor, parent_ident: Any) -> Entity:
        '''Look up the parent object.'''
        from ...libvirt.entity import Entity
        from ...libvirt.entity_access import EntityAccess

        if self.PARENT_ATTR is None or self.PARENT_NAME is None:
            raise RuntimeError

        parent = cast(EntityAccess[Entity], getattr(hv, self.PARENT_ATTR)).get(parent_ident)

        if not parent:
            LOGGER.error(f'Could not find { self.PARENT_NAME } "{ parent_ident }"')
            ctx.exit(ExitCode.PARENT_NOT_FOUND)

        return parent

    def get_sub_entity(self: Self, ctx: click.Context, hv: Hypervisor, parent_ident: Any, ident: Any) -> Entity:
        '''Look up an entity that is a child of another entity.'''
        parent = self.get_parent_obj(ctx, hv, parent_ident)

        return self.get_entity(ctx, parent, ident)

    def match_entities(self: Self, ctx: click.Context, parent: Entity | Hypervisor, match: MatchArgument) -> Iterable[Entity]:
        '''Match a set of entities.'''
        from ...libvirt.entity_access import EntityAccess

        return cast(EntityAccess, getattr(parent, self.LOOKUP_ATTR)).match(match)

    def match_sub_entities(self: Self, ctx: click.Context, hv: Hypervisor, parent_ident: Any, match: MatchArgument) -> Iterable[Entity]:
        '''Match a set of entities that are children of another entity.'''
        parent = self.get_parent_obj(ctx, hv, parent_ident)

        return self.match_entities(ctx, parent, match)
