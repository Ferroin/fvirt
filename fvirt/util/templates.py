# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Template handling for fvirt.

   Note that templating support is optional for fivrt. It requires jinja2
   and ruamel.yaml to be installed.'''

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    import jinja2


def get_environment(importer: Callable[..., ModuleType] = import_module) -> jinja2.Environment | None:
    '''Get a jinja2 Environment with our templates in it.

       If templating is not supported, this will return None.

       The result of this function is not cached. A new environment will
       be returned each time. If you expect to do a lot of templating,
       it’s more efficient to call this once and cache the result
       yourself.'''
    try:
        jinja2 = importer('jinja2')
    except ImportError:
        return None

    return jinja2.Environment(  # type: ignore
        loader=jinja2.PackageLoader('fvirt', 'templates'),
        autoescape=jinja2.select_autoescape(),
    )
