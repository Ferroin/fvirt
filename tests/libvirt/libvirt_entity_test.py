# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.entity

   Most of the code in this module is (intentionally) tested indirectly
   via tests for the various subclasses. This is done because nobody
   should be directly creating Entity instances without using the
   subclasses. However, a small handful of things need to be checked on
   the base class itself, and those are covered here.'''

from __future__ import annotations

import pytest

from fvirt.libvirt import FeatureNotSupported
from fvirt.libvirt.entity import Entity


def test_entity_default_template_info() -> None:
    '''Check that the default template info for an Entity is empty.'''
    assert Entity._get_template_info() is None


def test_entity_render_config_invalid_template() -> None:
    '''Check that Entity._render_config() correctly raises an error if no template is given.'''
    with pytest.raises(ValueError):
        Entity._render_config()


def test_entity_new_config_default() -> None:
    '''Check that Entity.new_config() raises a FeatureNotSupported exception by default.'''
    with pytest.raises(FeatureNotSupported):
        Entity.new_config(config=dict())
