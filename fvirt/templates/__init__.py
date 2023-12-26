# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Template handling for fvirt.

   Note that templating support is optional for fivrt. It requires a
   number of supplementary packages to be installed, which can be pulled
   in using the `templating` extra for fvirt..'''

from __future__ import annotations

import logging

from typing import Final

import jinja2

LOGGER: Final = logging.getLogger(__name__)


def get_environment() -> jinja2.Environment:
    '''Get a jinja2 Environment with our templates in it.

       The result of this function is not cached. A new environment will
       be returned each time. If you expect to do a lot of templating,
       it’s more efficient to call this once and cache the result
       yourself.'''
    return jinja2.Environment(
        loader=jinja2.PackageLoader('fvirt', 'templates'),
        autoescape=jinja2.select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def template_filter(name: str, /) -> bool:
    '''Filter for use with list_templates and compile_templates.'''
    if name.startswith('__') or \
       name.startswith('.') or \
       name.endswith('.py') or \
       name.endswith('.pyc') or \
       name.endswith('.pyo') or \
       name.endswith('.swp') or \
       name.endswith('~'):
        return False

    return True
