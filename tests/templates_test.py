# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.util.templates'''

from __future__ import annotations

from typing import TYPE_CHECKING

import jinja2

from fvirt.templates import get_environment, template_filter

if TYPE_CHECKING:
    from pathlib import Path


def test_get_environment() -> None:
    '''Check that get_environment() works correctly.'''
    env = get_environment()

    assert isinstance(env, jinja2.Environment)
    assert len(env.list_templates(filter_func=template_filter)) > 0


def test_templates(tmp_path: Path) -> None:
    '''Check that all templates compile correctly.'''
    env = get_environment()

    assert env is not None

    env.compile_templates(
        target=str(tmp_path),
        zip=None,
        ignore_errors=False,
        filter_func=template_filter,
    )
