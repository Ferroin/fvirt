# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Shared code for all tests.'''

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest

from lxml import etree
from ruamel.yaml import YAML as Yaml

YAML = Yaml(typ='safe')
CASE_DATA_PREFIX = Path(__file__).parent / 'data' / 'cases'


def get_test_cases(group: str) -> Mapping[str, Any]:
    '''Load test cases for the specified group.'''
    return cast(Mapping[str, Any], YAML.load(CASE_DATA_PREFIX / f'{group}.yaml'))


def compare_xml_trees(e1: etree._Element | etree._ElementTree, e2: etree._Element | etree._ElementTree) -> None:
    '''Compare two lxml.etree trees against each other.'''
    if isinstance(e1, etree._ElementTree):
        e1 = e1.getroot()

    if isinstance(e2, etree._ElementTree):
        e2 = e2.getroot()

    assert e1.tag == e2.tag

    if e1.text is None:
        assert e2.text is None
    elif e2.text is None:
        assert e1.text is None
    else:
        checked = False
        try:
            assert float(e1.text) == pytest.approx(float(e2.text))
            checked = True
        except ValueError:
            pass

        if not checked:
            assert e1.text == e2.text

    assert e1.tail == e2.tail
    assert e1.attrib == e2.attrib
    assert len(e1) == len(e2)

    for c1, c2 in zip(e1, e2):
        compare_xml_trees(c1, c2)
