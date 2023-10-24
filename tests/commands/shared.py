# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Shared code for tests for fvirt.commands'''

from __future__ import annotations

import importlib
import re

from pathlib import Path
from typing import TYPE_CHECKING

import click
import pytest

from fvirt.libvirt.entity import Entity
from fvirt.util.tables import Column
from fvirt.util.units import bytes_to_unit

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from fvirt.commands._base.group import Group
    from fvirt.commands._base.info import InfoItem

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


def check_list_entry(line: str, obj: Entity, cols: Sequence[Column]) -> None:
    '''Check a single entry in the list command output.'''
    values = line.split()

    assert len(values) == len(cols)

    for v, c in zip(values, cols):
        assert v == c.color(getattr(obj, c.prop, None))


def check_list_output(output: str, obj: Entity, cols: Sequence[Column]) -> None:
    '''Check that the list command works correctly.'''
    lines = output.splitlines()

    headings = lines[0].split()

    assert len(headings) == len(cols)

    for h, c in zip(headings, cols):
        assert h == c.title

    assert re.match('^-+?$', lines[1])

    check_list_entry(lines[2], obj, cols)


def check_info_items(items: tuple[InfoItem, ...], sample: Entity) -> None:
    '''Check that a list of info items is valid for a given entity.'''
    assert isinstance(items, tuple)

    for item in items:
        assert isinstance(item.name, str)
        assert isinstance(item.prop, str)
        assert item.prop in dir(sample)


def check_info_output(output: str, items: tuple[InfoItem, ...], entity: Entity, header: str) -> None:
    '''Check the output from an info command.'''
    assert header == output.splitlines()[0]

    for item in items:
        match = re.search(f'^  { item.name }: (.+?)$', output, re.MULTILINE)
        prop = getattr(entity, item.prop, None)

        if prop is not None and prop != '':
            assert match, f'No match found for { item.name }.'
            if item.use_units:
                ev, eu = bytes_to_unit(prop)
                av, au = match[1].split(' ')
                decimal_places = len(av.split('.')[1])
                assert eu == au
                assert ev == pytest.approx(float(av), abs=10 ** -decimal_places)
            else:
                assert match[1] == item.color(prop)
        else:
            assert match is None, f'Found erroneous entry for { item.name }.'
