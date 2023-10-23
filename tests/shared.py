# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Shared code for all tests.'''

from __future__ import annotations

import pytest

from lxml import etree


def compare_xml_trees(e1: etree._Element, e2: etree._Element) -> None:
    '''Compare two lxml.etree trees against each other.'''
    assert e1.tag == e2.tag

    if e1.text is None:
        assert e2.text is None
    elif e2.text is None:
        assert e1.text is None
    else:
        try:
            assert float(e1.text) == pytest.approx(float(e2.text))
        except ValueError:
            assert e1.text == e2.text

    assert e1.tail == e2.tail
    assert e1.attrib == e2.attrib
    assert len(e1) == len(e2)

    for c1, c2 in zip(e1, e2):
        compare_xml_trees(c1, c2)
