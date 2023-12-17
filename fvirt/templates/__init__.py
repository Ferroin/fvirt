# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Template handling for fvirt.

   Note that templating support is optional for fivrt. It requires a
   number of supplementary packages to be installed, which can be pulled
   in using the `templating` extra for fvirt..'''

from __future__ import annotations

import functools
import logging

from importlib import import_module
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    import jinja2

LOGGER: Final = logging.getLogger(__name__)


@functools.cache
def check_for_templating(importer: Callable[..., ModuleType] = import_module) -> bool:
    '''Check if templating is actually supported.

       The result of this function is cached.'''
    try:
        importer('jinja2')
        importer('psutil')
        importer('pydantic')
    except ImportError:
        LOGGER.info('Templating support is not available.')
        return False

    return True


def get_environment(importer: Callable[..., ModuleType] = import_module) -> jinja2.Environment | None:
    '''Get a jinja2 Environment with our templates in it.

       If templating is not supported, this will return None. This checks
       for _all_ required templating dependencies, not just jinja2.

       The result of this function is not cached. A new environment will
       be returned each time. If you expect to do a lot of templating,
       it’s more efficient to call this once and cache the result
       yourself. If you just want to check if templating support is
       available, use check_for_templating() instead.'''
    if not check_for_templating(importer):
        return None

    LOGGER.debug('Generating jinja2 environment.')

    import jinja2

    return jinja2.Environment(
        loader=jinja2.PackageLoader('fvirt', 'templates'),
        autoescape=jinja2.select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def template_filter(name: str) -> bool:
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
