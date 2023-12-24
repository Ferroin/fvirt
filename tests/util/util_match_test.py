# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''tests for fvirt.util.match'''

from __future__ import annotations

from typing import Self

from lxml import etree

from fvirt.util.match import MatchTarget

TMPL = '''
<root>
    <name>name{idx}</name>
    <a>
        <b>{idx}</b>
    </a>
    <c d='{idx}' />
</root>
'''.lstrip().rstrip()

INDICES = range(0, 3)


class MatchTest:
    '''Mock object for testing MatchTarget instances.'''
    def __init__(self: Self, idx: int) -> None:
        self.name = f'name{idx}'
        self.id = idx
        self.config = etree.XML(TMPL.format(idx=idx))


TEST_OBJECTS = tuple(
    MatchTest(x) for x in INDICES
)


def test_match_target_property_str() -> None:
    '''Test MatchTarget behavior for properties.'''
    target = MatchTarget(property='name')

    results = {
        target.get_value(o) for o in TEST_OBJECTS  # type: ignore
    }

    assert results == {
        f'name{x}' for x in INDICES
    }


def test_match_target_property_int() -> None:
    '''Test MatchTarget behavior for properties.'''
    target = MatchTarget(property='id')

    results = {
        target.get_value(o) for o in TEST_OBJECTS  # type: ignore
    }

    assert results == {
        str(x) for x in INDICES
    }


def test_match_target_path1() -> None:
    '''Check MatchTarget with top level path.'''
    target = MatchTarget(xpath=etree.XPath('./name/text()'))

    results = {
        target.get_value(o) for o in TEST_OBJECTS  # type: ignore
    }

    assert results == {
        f'name{x}' for x in INDICES
    }


def test_match_target_path2() -> None:
    '''Check MatchTarget with multi-level path.'''
    target = MatchTarget(xpath=etree.XPath('./a/b/text()'))

    results = {
        target.get_value(o) for o in TEST_OBJECTS  # type: ignore
    }

    assert results == {
        str(x) for x in INDICES
    }


def test_match_target_path3() -> None:
    '''Check MatchTarget with attribute path.'''
    target = MatchTarget(xpath=etree.XPath('./c/@d'))

    results = {
        target.get_value(o) for o in TEST_OBJECTS  # type: ignore
    }

    assert results == {
        str(x) for x in INDICES
    }
