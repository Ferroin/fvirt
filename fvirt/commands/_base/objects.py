# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command mixins for handling various object types.'''

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self, TypeGuard, cast

import click

from .exitcode import ExitCode
from ...libvirt.entity_access import EntityAccess

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ...libvirt import Hypervisor
    from ...libvirt.entity import Entity
    from ...util.match import MatchArgument


def is_object_mixin(obj: Any) -> TypeGuard[ObjectMixin]:
    '''Indicate that a given object is an ObjectMixin.

       Commands that use ObjectMixin functionality should assert this
       in their __init__ method.'''
    if not hasattr(obj, '_OBJ_MIXIN'):
        raise RuntimeError

    return True


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

    def mixin_params(self: Self, required: bool = False) -> tuple[click.Argument, ...]:
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

    def mixin_parent_params(self: Self) -> tuple[click.Argument, ...]:
        '''Return a tuple of arguments for specifying the parent.'''
        return (click.Argument(
            param_decls=('parent',),
            nargs=1,
            metavar=self.PARENT_METAVAR,
            required=True
        ),)

    def get_entity(self: Self, ctx: click.Context, parent: Entity | Hypervisor, ident: Any) -> Entity:
        '''Look up an entity based on an identifier.'''
        entity = cast(EntityAccess, getattr(parent, self.LOOKUP_ATTR)).get(ident)

        if entity is None:
            click.echo(f'Could not find { self.NAME } "{ ident }".', err=True)
            ctx.exit(ExitCode.ENTITY_NOT_FOUND)

        return entity

    def get_parent_obj(self: Self, ctx: click.Context, hv: Hypervisor, parent_ident: Any) -> Entity:
        '''Look up the parent object.'''
        if self.PARENT_ATTR is None or self.PARENT_NAME is None:
            raise RuntimeError

        parent = cast(EntityAccess, getattr(hv, self.PARENT_ATTR)).get(parent_ident)

        if not parent:
            click.echo(f'Could not find { self.PARENT_NAME } "{ parent_ident }".', err=True)
            ctx.exit(ExitCode.PARENT_NOT_FOUND)

        return parent

    def get_sub_entity(self: Self, ctx: click.Context, hv: Hypervisor, parent_ident: Any, ident: Any) -> Entity:
        '''Look up an entity that is a child of another entity.'''
        parent = self.get_parent_obj(ctx, hv, parent_ident)

        return self.get_entity(ctx, parent, ident)

    def match_entities(self: Self, ctx: click.Context, parent: Entity | Hypervisor, match: MatchArgument) -> Iterable[Entity]:
        '''Match a set of entities.'''
        return cast(EntityAccess, getattr(parent, self.LOOKUP_ATTR)).match(match)

    def match_sub_entities(self: Self, ctx: click.Context, hv: Hypervisor, parent_ident: Any, match: MatchArgument) -> Iterable[Entity]:
        '''Match a set of entities that are children of another entity.'''
        parent = self.get_parent_obj(ctx, hv, parent_ident)

        return self.match_entities(ctx, parent, match)


class DomainMixin(ObjectMixin):
    '''Mixin for commands that operate on domains.'''
    @property
    def NAME(self: Self) -> str: return 'domain'

    @property
    def METAVAR(self: Self) -> str: return 'DOMAIN'

    @property
    def LOOKUP_ATTR(self: Self) -> str: return 'domains'

    @property
    def DEFINE_METHOD(self: Self) -> str: return 'defineDomain'

    @property
    def CREATE_METHOD(self: Self) -> str: return 'createDomain'


class StoragePoolMixin(ObjectMixin):
    '''Mixin for commands that operate on domains.'''
    @property
    def NAME(self: Self) -> str: return 'storage pool'

    @property
    def METAVAR(self: Self) -> str: return 'POOL'

    @property
    def LOOKUP_ATTR(self: Self) -> str: return 'pools'

    @property
    def DEFINE_METHOD(self: Self) -> str: return 'defineStoragePool'

    @property
    def CREATE_METHOD(self: Self) -> str: return 'createStoragePool'


class VolumeMixin(ObjectMixin):
    @property
    def NAME(self: Self) -> str: return 'volume'

    @property
    def METAVAR(self: Self) -> str: return 'VOLUME'

    @property
    def LOOKUP_ATTR(self: Self) -> str: return 'volumes'

    @property
    def DEFINE_METHOD(self: Self) -> str: return 'defineVolume'

    @property
    def PARENT_NAME(self: Self) -> str: return 'storage pool'

    @property
    def PARENT_METAVAR(self: Self) -> str: return 'POOL'

    @property
    def PARENT_ATTR(self: Self) -> str: return 'pools'
