# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.util.templates'''

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

import pytest

from fvirt.templates import get_environment, template_filter

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType


def test_get_environment_no_jinja2() -> None:
    '''Check that we return None with no jinja2 available.'''
    def importer(name: str) -> ModuleType:
        match name:
            case 'jinja2':
                raise ImportError
            case _:
                return import_module(name)

    assert get_environment(importer=importer) is None


def test_get_environment() -> None:
    '''Check that get_environment() works correctly.'''
    jinja2 = pytest.importorskip('jinja2', reason='Cannot run test without jinja2.')

    env = get_environment()

    assert isinstance(env, jinja2.Environment)
    assert len(env.list_templates(filter_func=template_filter)) > 0


def test_templates(tmp_path: Path) -> None:
    '''Check that all templates compile correctly.'''
    pytest.importorskip('jinja2', reason='Cannot run test without jinja2.')

    env = get_environment()

    assert env is not None

    env.compile_templates(
        target=str(tmp_path),
        zip=None,
        ignore_errors=False,
        filter_func=template_filter,
    )
