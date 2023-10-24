# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.domain'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any, Type
from uuid import UUID

import pytest

from lxml import etree

from fvirt.libvirt import EntityNotRunning, Hypervisor, LifecycleResult
from fvirt.libvirt.domain import MATCH_ALIASES, Domain, DomainState
from fvirt.util.match import MatchArgument, MatchTarget

from .shared import (check_entity_access_get, check_entity_access_iterable, check_entity_access_mapping, check_entity_access_match,
                     check_entity_format, check_match_aliases, check_runnable_destroy, check_runnable_start, check_undefine)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import _GeneratorContextManager


def test_check_match_aliases(test_dom: Domain) -> None:
    '''Check typing for match aliases.'''
    check_match_aliases(MATCH_ALIASES, test_dom)


def test_format(test_dom: Domain) -> None:
    '''Check that formatting a Domain instance can be formatted.'''
    # TODO: This should use a live domain for better test coverage.
    check_entity_format(test_dom)


def test_name(test_dom: Domain) -> None:
    '''Check the name attribute.'''
    assert isinstance(test_dom.name, str)


def test_id(test_dom: Domain) -> None:
    assert test_dom.running == True  # noqa: E712
    assert isinstance(test_dom.id, int)
    assert test_dom.id > 0
    assert test_dom.destroy() == LifecycleResult.SUCCESS
    assert test_dom.id == -1


def test_state(test_dom: Domain) -> None:
    '''Check the state attribute.'''
    assert isinstance(test_dom.state, DomainState)
    assert test_dom.state == DomainState.RUNNING
    assert test_dom.destroy() == LifecycleResult.SUCCESS
    assert test_dom.state != DomainState.RUNNING


def test_undefine(test_dom: Domain) -> None:
    '''Check that undefining a domain works.'''
    check_undefine(test_dom._hv, 'domains', test_dom)


def test_reset(test_dom: Domain) -> None:
    '''Check that resetting a domain works.'''
    # TODO: Should be redesigned once we have true live domain testing.
    assert test_dom.running == True  # noqa: E712

    result = test_dom.reset()

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert test_dom.running == True  # noqa: E712


def test_stop(test_dom: Domain) -> None:
    '''Check that stopping a domain works.'''
    check_runnable_destroy(test_dom)


def test_start(test_dom: Domain) -> None:
    '''Check that starting a domain works.'''
    check_runnable_start(test_dom)


def test_shutdown(test_dom: Domain) -> None:
    '''Check that shutting down a domain works.'''
    # TODO: Should be redesigned once we have true live domain testing.
    assert test_dom.running == True  # noqa: E712

    result = test_dom.shutdown(timeout=0, force=False, idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert test_dom.running == False  # noqa: E712

    result = test_dom.shutdown(timeout=0, force=False, idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert test_dom.running == False  # noqa: E712

    result = test_dom.shutdown(timeout=0, force=True, idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert test_dom.running == False  # noqa: E712

    result = test_dom.shutdown(timeout=0, force=False, idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert test_dom.running == False  # noqa: E712

    result = test_dom.shutdown(timeout=0, force=True, idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert test_dom.running == False  # noqa: E712


def test_shutdown_timeouts(test_dom: Domain) -> None:
    '''Check that timeout handling for the domain shutdown operation works.'''
    # TODO: Should be redesigned once we have true live domain testing.
    assert test_dom.running == True  # noqa: E712

    result = test_dom.shutdown(timeout=1, force=False, idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert test_dom.running == False  # noqa: E712


def test_managed_save(test_dom: Domain) -> None:
    '''Check that the managed save functionality works.'''
    # TODO: Should be redesigned once we have true live domain testing.
    assert test_dom.running == True  # noqa: E712
    assert test_dom.hasManagedSave == False  # noqa: E712

    result = test_dom.managedSave(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert test_dom.running == False  # noqa: E712
    assert test_dom.hasManagedSave == True  # noqa: E712

    result = test_dom.managedSave(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert test_dom.running == False  # noqa: E712
    assert test_dom.hasManagedSave == True  # noqa: E712

    result = test_dom.managedSave(idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert test_dom.running == False  # noqa: E712
    assert test_dom.hasManagedSave == True  # noqa: E712

    result = test_dom.start()

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert test_dom.running == True  # noqa: E712
    assert test_dom.hasManagedSave == False  # noqa: E712

    test_dom.destroy()

    assert test_dom.running == False  # noqa: E712
    assert test_dom.hasManagedSave == False  # noqa: E712

    with pytest.raises(EntityNotRunning):
        test_dom.managedSave()


@pytest.mark.xfail(reason='Cannot be tested without live domain testing.')
def test_domain_console() -> None:
    '''Test that domain console handling works correctly.'''
    assert False


@pytest.mark.xfail(reason='Cannot be tested without live domain testing.')
def test_domain_xslt(test_domain: Domain) -> None:
    '''Test that applying an XSLT document to a domain modifies it.'''
    assert False


def test_domain_access_iterable(test_hv: Hypervisor, serial: Callable[[str], _GeneratorContextManager[None]]) -> None:
    '''Test domain entity access behavior.'''
    with serial('domain'):
        check_entity_access_iterable(test_hv.domains, Domain)


@pytest.mark.parametrize('k', (
    1,
    '1',
    'test',
    '6695eb01-f6a4-8304-79aa-97f2502e193f',
    UUID('6695eb01-f6a4-8304-79aa-97f2502e193f'),
))
def test_domain_access_get(test_hv: Hypervisor, k: int | str | UUID) -> None:
    '''Test domain entity access get method.'''
    check_entity_access_get(test_hv.domains, k, Domain)


@pytest.mark.parametrize('m', (
    (MatchTarget(property='name'), re.compile('^test$')),
    (MatchTarget(property='state'), re.compile('^running$')),
    (MatchTarget(property='persistent'), re.compile('^True$')),
    (MatchTarget(xpath=etree.XPath('./os/type/text()[1]')), re.compile('^hvm$')),
))
def test_domain_access_match(test_hv: Hypervisor, m: MatchArgument) -> None:
    '''Test domain entity access match method.'''
    check_entity_access_match(test_hv.domains, m, Domain)


@pytest.mark.parametrize('p, k, c', (
    (
        'by_name',
        (
            'test',
        ),
        str
    ),
    (
        'by_uuid',
        (
            '6695eb01-f6a4-8304-79aa-97f2502e193f',
            UUID('6695eb01-f6a4-8304-79aa-97f2502e193f'),
        ),
        UUID,
    ),
    (
        'by_id',
        (
            1,
        ),
        int,
    ),
))
def test_domain_access_mapping(test_hv: Hypervisor, p: str, k: Sequence[Any], c: Type[object]) -> None:
    '''Test domain entity access mappings.'''
    check_entity_access_mapping(test_hv.domains, p, k, c, Domain)
