# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.domain'''

from __future__ import annotations

import re

from time import sleep
from typing import TYPE_CHECKING, Any, Type
from uuid import UUID

import pytest

from lxml import etree

from fvirt.libvirt import Domain, DomainState, EntityNotRunning, Hypervisor, InvalidConfig, LifecycleResult
from fvirt.util.match import MatchArgument, MatchTarget

from .shared import (check_entity_access_get, check_entity_access_iterable, check_entity_access_mapping, check_entity_access_match,
                     check_entity_format, check_match_aliases, check_runnable_destroy, check_runnable_start, check_undefine, check_xslt)
from ..shared import compare_xml_trees

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from contextlib import _GeneratorContextManager


def test_check_match_aliases(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check typing for match aliases.'''
    check_match_aliases(Domain.MATCH_ALIASES, test_dom[0])


def test_equality(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Test that domain equality checks work correctly.'''
    # TODO: Needs to be expanded to use a live domain for better test coverage.
    dom, hv = test_dom

    assert dom == dom

    assert dom != ''

    dom2 = hv.domains.get(dom.name)

    assert dom == dom2


def test_self_wrap(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that instantiating a Domain with another Domain instance produces an equal Domain.'''
    dom, _ = test_dom
    assert Domain(dom) == dom


def test_format(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that formatting a Domain instance can be formatted.'''
    # TODO: This should use a live domain for better test coverage.
    dom, _ = test_dom
    check_entity_format(dom)


def test_name(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check the name attribute.'''
    dom, _ = test_dom
    assert isinstance(dom.name, str)


def test_id(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check the id attribute.'''
    dom, _ = test_dom
    assert dom.running == True  # noqa: E712
    assert isinstance(dom.id, int)
    assert dom.id > 0
    assert dom.destroy() == LifecycleResult.SUCCESS
    assert dom.id == -1


def test_domain_state() -> None:
    '''Check the DomainState enumerable.'''
    for s in DomainState:
        assert isinstance(s.value, int)

    assert len({s.value for s in DomainState}) == len(DomainState), 'duplicate values in DomainState'
    assert len({str(s) for s in DomainState}) == len(DomainState), 'duplicate string representations in DomainState'


def test_state(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check the state attribute.'''
    dom, _ = test_dom
    assert isinstance(dom.state, DomainState)
    assert dom.state == DomainState.RUNNING
    assert dom.destroy() == LifecycleResult.SUCCESS
    assert dom.state != DomainState.RUNNING


def test_define(test_hv: Hypervisor, test_dom_xml: Callable[[], str]) -> None:
    '''Check that defining a domain works.'''
    xml = test_dom_xml()

    result = test_hv.define_domain(xml)

    assert isinstance(result, Domain)


def test_config_raw(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Test the config_raw property.'''
    dom, _ = test_dom
    conf = dom.config_raw

    assert isinstance(conf, str)

    new_conf = conf.replace("clock offset='utc'", "clock offset='localtime'")

    assert conf != new_conf

    dom.config_raw = new_conf

    assert dom.config_raw != conf
    assert dom.config_raw == new_conf


def test_invalid_config_raw(test_dom: tuple[Domain, Hypervisor], capfd: pytest.CaptureFixture) -> None:
    '''Test trying to use a bogus config with the config_raw property.'''
    dom, _ = test_dom
    conf = dom.config_raw

    assert isinstance(conf, str)

    bad_conf = conf.replace("clock offset='utc'", "clock offset='foo'")

    with pytest.raises(InvalidConfig):
        dom.config_raw = bad_conf


def test_config(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Test the config property.'''
    dom, _ = test_dom
    conf = dom.config

    assert isinstance(conf, etree._ElementTree)

    e = conf.find('/clock')
    assert e is not None

    e.attrib['offset'] = 'localtime'

    dom.config = conf

    compare_xml_trees(dom.config, conf)


def test_invalid_config(test_dom: tuple[Domain, Hypervisor], capfd: pytest.CaptureFixture) -> None:
    '''Test trying to use a bogus config with the config property.'''
    dom, _ = test_dom
    conf = dom.config

    assert isinstance(conf, etree._ElementTree)

    e = conf.find('/clock')
    assert e is not None

    e.attrib['offset'] = 'foo'

    with pytest.raises(InvalidConfig):
        dom.config = conf


def test_config_raw_live(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Test that the config_raw_live property works as expected.'''
    dom, _ = test_dom
    conf = dom.config_raw
    live_conf = dom.config_raw_live

    assert isinstance(conf, str)
    assert isinstance(live_conf, str)

    new_conf = conf.replace("clock offset='utc'", "clock offset='localtime'")

    assert conf != new_conf

    dom.config_raw = new_conf

    assert dom.config_raw == new_conf
    assert dom.config_raw_live == live_conf


def test_config_live(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Test that the config_raw_live property works as expected.'''
    dom, _ = test_dom
    conf = dom.config
    live_conf = dom.config_live

    assert isinstance(conf, etree._ElementTree)
    assert isinstance(live_conf, etree._ElementTree)

    e = conf.find('/clock')
    assert e is not None

    e.attrib['offset'] = 'localtime'

    dom.config = conf

    compare_xml_trees(dom.config, conf)
    compare_xml_trees(dom.config_live, live_conf)


def test_create(live_hv: Hypervisor, live_dom_xml: Callable[[], str], serial: Callable[[str], _GeneratorContextManager]) -> None:
    '''Check that creating a domain works.'''
    xml = live_dom_xml()

    with serial('live-domain'):
        result = live_hv.create_domain(xml)

    try:
        assert isinstance(result, Domain)
        assert result.running
    finally:
        result.destroy()
        result.undefine()


def test_undefine(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that undefining a domain works.'''
    dom, hv = test_dom
    check_undefine(hv, 'domains', dom)


def test_reset(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that resetting a domain works.'''
    # TODO: Should be redesigned once we have the ability to interact with the domain console.
    dom, _ = test_dom
    assert dom.running == True  # noqa: E712

    result = dom.reset()

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert dom.running == True  # noqa: E712


def test_stop(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that stopping a domain works.'''
    dom, _ = test_dom
    check_runnable_destroy(dom)


def test_start(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that starting a domain works.'''
    dom, _ = test_dom
    check_runnable_start(dom)


def test_shutdown(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that shutting down a domain works.'''
    dom, _ = test_dom
    assert dom.running == True  # noqa: E712

    result = dom.shutdown(timeout=0, force=False, idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert dom.running == False  # noqa: E712

    result = dom.shutdown(timeout=0, force=False, idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert dom.running == False  # noqa: E712

    result = dom.shutdown(timeout=0, force=True, idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert dom.running == False  # noqa: E712

    result = dom.shutdown(timeout=0, force=False, idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert dom.running == False  # noqa: E712

    result = dom.shutdown(timeout=0, force=True, idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert dom.running == False  # noqa: E712


def test_shutdown_timeouts(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that timeout handling for the domain shutdown operation works.'''
    dom, _ = test_dom
    assert dom.running == True  # noqa: E712

    result = dom.shutdown(timeout=1, force=False, idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert dom.running == False  # noqa: E712


@pytest.mark.slow
@pytest.mark.parametrize('opts, expected, delay', (
    (
        {
            'timeout': 0,
            'force': True,
        },
        LifecycleResult.FORCED,
        0,
    ),
    (
        {
            'timeout': 15,
            'force': False,
        },
        LifecycleResult.SUCCESS,
        0,
    ),
    (
        {
            'timeout': None,
            'force': False,
        },
        LifecycleResult.SUCCESS,
        15,
    ),
    (
        {
            'timeout': 0,
            'force': False,
        },
        LifecycleResult.TIMED_OUT,
        15,
    ),
    (
        {
            'timeout': -1,
            'force': False,
        },
        LifecycleResult.SUCCESS,
        0,
    ),
))
def test_live_shutdown(opts: Mapping[str, Any], expected: LifecycleResult, delay: int, live_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that shutting down a domain works.'''
    dom, _ = live_dom
    iter_delay = 0.2

    dom.start(idempotent=True)

    assert dom.running == True  # noqa: E712
    sleep(3)
    assert dom.running == True  # noqa: E712

    result = dom.shutdown(**opts)

    assert isinstance(result, LifecycleResult)
    assert result == expected

    t = 0.0
    while t < delay:
        if not dom.running:
            break

        t += iter_delay
        sleep(iter_delay)

    assert dom.running == False  # noqa: E712


def test_managed_save(test_dom: tuple[Domain, Hypervisor]) -> None:
    '''Check that the managed save functionality works.'''
    # TODO: Should be redesigned once we have domain console interaction.
    dom, _ = test_dom
    assert dom.running == True  # noqa: E712
    assert dom.has_managed_save == False  # noqa: E712

    result = dom.managed_save(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert dom.running == False  # noqa: E712
    assert dom.has_managed_save == True  # noqa: E712

    result = dom.managed_save(idempotent=False)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.NO_OPERATION
    assert dom.running == False  # noqa: E712
    assert dom.has_managed_save == True  # noqa: E712

    result = dom.managed_save(idempotent=True)

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert dom.running == False  # noqa: E712
    assert dom.has_managed_save == True  # noqa: E712

    result = dom.start()

    assert isinstance(result, LifecycleResult)
    assert result == LifecycleResult.SUCCESS
    assert dom.running == True  # noqa: E712
    assert dom.has_managed_save == False  # noqa: E712

    dom.destroy()

    assert dom.running == False  # noqa: E712
    assert dom.has_managed_save == False  # noqa: E712

    with pytest.raises(EntityNotRunning):
        dom.managed_save()


@pytest.mark.slow
@pytest.mark.xfail(reason='Apparent bug in console handling code.''')
def test_domain_console(live_dom: tuple[Domain, Hypervisor]) -> None:
    '''Test that domain console handling works correctly.'''
    dom, _ = live_dom

    dom.start()
    assert dom.running
    sleep(3)

    console = dom.console()

    console.read(-1)

    console.write(b'\n')

    output = console.read(-1)

    assert len(output) > 0
    assert output[-4:] == b'~ #'

    console.write(b'poweroff\n')

    sleep(3)

    assert not dom.running


def test_domain_xslt(test_dom: tuple[Domain, Hypervisor], xslt_doc_factory: Callable[[str, str], str]) -> None:
    '''Test that applying an XSLT document to a domain modifies it.'''
    dom, _ = test_dom
    check_xslt(dom, 'on_crash', 'restart', xslt_doc_factory)


def test_domain_access_iterable(test_hv: Hypervisor, serial: Callable[[str], _GeneratorContextManager[None]]) -> None:
    '''Test domain entity access behavior.'''
    with serial('test-domain'):
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


@pytest.mark.parametrize('data', (
    {
        'name': 'test',
        'type': 'test',
        'memory': 65536,
        'os': {
            'variant': 'test',
            'arch': 'i686',
        },
    },
    {
        'name': 'test',
        'type': 'lxc',
        'memory': 65536,
        'os': {
            'variant': 'container',
            'init': '/sbin/init',
        },
    },
    {
        'name': '100',
        'type': 'vz',
        'memory': 65536,
        'os': {
            'variant': 'container',
            'init': '/sbin/init',
        },
    },
    {
        'name': 'test',
        'type': 'kvm',
        'memory': 65536,
        'vcpu': 4,
        'cpu': {},
        'os': {
            'variant': 'firmware',
            'firmware': 'efi',
            'arch': 'x86_64',
        },
    },
    {
        'name': 'test',
        'type': 'xen',
        'memory': 65536,
        'vcpu': 4,
        'cpu': {},
        'os': {
            'variant': 'host',
            'bootloader': '/usr/bin/test_loader',
            'type': 'linux',
        },
    },
))
def test_new_config(data: Mapping, virt_xml_validate: Callable[[str], None]) -> None:
    '''Test domain templating.'''
    doc = Domain.new_config(config=data)

    assert isinstance(doc, str)

    virt_xml_validate(doc)
