# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Shared functions for fvirt.libvirt tests.'''

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Type

from lxml import etree

from fvirt.libvirt import Hypervisor, LifecycleResult
from fvirt.libvirt.entity import Entity, RunnableEntity
from fvirt.libvirt.entity_access import EntityAccess, EntityMap
from fvirt.util.match import MatchAlias, MatchArgument

XSLT_DATA = '''
<?xml version='1.1'?>
<xsl:stylesheet xmlns:xsl='http://www.w3.org/1999/XSL/Transform' version='1.0'>
    <xsl:output method='xml' encoding='utf-8'/>
    <xsl:template match="node()|@*">
        <xsl:copy>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
    </xsl:template>
    <xsl:template match='{path}/text()'>
        <xsl:text>{value}</xsl:text>
    </xsl:template>
</xsl:stylesheet>
'''.lstrip().rstrip()


def check_match_aliases(aliases: Mapping[str, MatchAlias], entity: Entity) -> None:
    '''Check a set of match aliases.'''
    assert isinstance(aliases, dict)

    for k, v in aliases.items():
        assert isinstance(k, str)
        assert isinstance(v, MatchAlias)
        assert v.property is not None
        # Can't use hasattr() here because our descriptors raise AttributeError if the associated value is not in the object config.
        assert v.property in dir(entity)
        assert v.desc is not None


def check_entity_format(entity: Entity) -> None:
    '''Check that Entity instances properly handle format().'''
    props = entity._format_properties

    for prop in props:
        assert isinstance(prop, str)
        assert prop in dir(entity)

        if hasattr(entity, prop):
            result = format(entity, '{' + prop + '}')
            assert result == str(getattr(entity, prop))


def check_runnable_start(entity: RunnableEntity) -> None:
    '''Check that the start method for a RunnableEntity works.'''
    assert entity.persistent == True  # noqa: E712

    entity.destroy(idempotent=True)

    assert entity.running == False  # noqa: E712

    result = entity.start()

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert entity.running == True  # noqa: E712

    result = entity.start(idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert entity.running == True  # noqa: E712

    result = entity.start(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert entity.running == True  # noqa: E712


def check_runnable_destroy(entity: RunnableEntity) -> None:
    '''Check that the destroy method for a RunnableEntity works.'''
    assert entity.persistent == True  # noqa: E712
    assert entity.running == True  # noqa: E712

    result = entity.destroy()

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert entity.running == False  # noqa: E712

    result = entity.destroy(idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert entity.running == False  # noqa: E712

    result = entity.destroy(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert entity.running == False  # noqa: E712


def check_undefine(parent: Hypervisor | Entity, prop: str, entity: Entity) -> None:
    '''Check that a Entity can be undefined propery.'''
    assert entity.valid == True  # noqa: E712

    name = entity.name

    if isinstance(entity, RunnableEntity):
        if entity.running:
            entity.destroy()

    should_be_valid = not entity._mark_invalid_on_undefine

    result = entity.undefine(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert entity.valid == should_be_valid
    assert getattr(parent, prop).get(name) is None

    result = entity.undefine(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert entity.valid == should_be_valid
    assert getattr(parent, prop).get(name) is None

    result = entity.undefine(idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert entity.valid == should_be_valid
    assert getattr(parent, prop).get(name) is None


def check_xslt(target: Entity, path: str, value: str) -> None:
    '''Check that applying an XSLT document to an entity works.'''
    assert not path.startswith('/')

    e = target.config.find(f'/{path}')
    assert e is not None
    old_value = e.text

    target.apply_xslt(etree.XSLT(etree.XML(XSLT_DATA.format(path=path, value=value))))
    e = target.config.find(f'/{path}')

    assert e is not None
    assert e.text == value

    target.apply_xslt(etree.XSLT(etree.XML(XSLT_DATA.format(path=path, value=old_value))))
    e = target.config.find(f'/{path}')

    assert e is not None
    assert e.text == old_value


def check_entity_access_iterable(ea: EntityAccess, target_cls: Type[Entity]) -> None:
    '''Check that an EntityAccess instance iterates correctly.'''
    assert isinstance(ea, Iterable)

    len1 = len(ea)
    len2 = len([x for x in ea])

    assert len1 == len2
    assert all([isinstance(e, target_cls) for e in ea])


def check_entity_access_get(ea: EntityAccess, target: Any, target_cls: Type[Entity]) -> None:
    '''Check that an EntityAccess ‘get’ method works.'''
    entity = ea.get(target)

    assert entity is not None
    assert isinstance(entity, target_cls)


def check_entity_access_match(ea: EntityAccess, target: MatchArgument, target_cls: Type[Entity]) -> None:
    '''Check that an EntityAccess 'match' method works.'''
    entities = ea.match(target)

    assert isinstance(ea, Iterable)

    entity_list = [x for x in entities]

    assert len(entity_list) > 0
    assert all([isinstance(x, target_cls) for x in entity_list])


def check_entity_access_mapping(ea: EntityAccess, prop: str, keys: Sequence[Any], key_cls: Type[object], target_cls: Type[Entity]) -> None:
    '''Check that an EntityMap on an EntityAccess instance works.'''
    assert hasattr(ea, prop)

    em = getattr(ea, prop)

    assert isinstance(em, EntityMap)

    assert all([isinstance(k, key_cls) for k in em.keys()])
    assert all([isinstance(v, target_cls) for v in em.values()])

    for k in keys:
        assert em[k]
