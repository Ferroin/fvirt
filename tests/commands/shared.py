# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Shared code for tests for fvirt.commands'''

from __future__ import annotations

import importlib

from pathlib import Path
from typing import TYPE_CHECKING

import click

from fvirt.libvirt.entity import Entity
from fvirt.util.tables import Column

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from fvirt.commands._base.group import Group

SRC_ROOT = Path(__file__).parents[2]


def check_lazy_commands(group: Group, modpath: Path) -> None:
    '''Check that lazy loaded commands are all correct for a given group and module.'''
    for name, cmdpath in group.lazy_commands.items():
        assert isinstance(name, str)
        assert isinstance(cmdpath, str)
        assert cmdpath.startswith('fvirt.commands.')

        modname, cmd_name = cmdpath.rsplit('.', 1)
        mod = importlib.import_module(modname)
        cmd = getattr(mod, cmd_name)

        assert isinstance(cmd, click.BaseCommand)
        assert cmd.name == name

        cmdfspath = Path(cmdpath.replace('.', '/').replace('fvirt', str(SRC_ROOT / 'fvirt')))

        assert modpath in cmdfspath.parents

    cmdpaths = {x.rpartition('.')[0] for x in group.lazy_commands.values()}

    for p in modpath.iterdir():
        if not p.match('*.py') or p.match('__init__.py'):
            continue

        cmdpath = '.'.join(p.relative_to(SRC_ROOT).with_suffix('').parts)

        assert cmdpath in cmdpaths


def check_columns(cols: Mapping[str, Column], sample: Entity) -> None:
    '''CHeck that a mapping of columns is valid.'''
    for k, v in cols.items():
        assert isinstance(k, str)
        assert isinstance(v, Column)
        assert v.prop in dir(sample)

    assert len({x.title for x in cols.values()}) == len(cols)


def check_default_columns(cols: Mapping[str, Column], default: Sequence[str]) -> None:
    '''Check that a list of default columns is valid.'''
    for k in default:
        assert k in cols
