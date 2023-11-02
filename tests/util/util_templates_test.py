# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.util.templates'''

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

import pytest

from fvirt.util.templates import get_environment

if TYPE_CHECKING:
    from types import ModuleType


def test_get_environment_no_jinja2() -> None:
    '''Check that we return None with no jinja2 available.'''
    def importer(name: str) -> ModuleType:
        match name:
            case 'jinja2':
                raise ImportError
            case _:
                return import_module(name)

    assert get_environment(importer) is None


def test_get_environment() -> None:
    '''Check that get_environment() works correctly.'''
    jinja2 = pytest.importorskip('jinja2', reason='Cannot run test without jinja2.')

    env = get_environment()

    assert isinstance(env, jinja2.Environment)
    assert len(env.list_templates()) > 0
