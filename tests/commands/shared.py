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

from fvirt.commands._base.objects import DisplayProperty, ObjectMixin
from fvirt.libvirt.entity import Entity
from fvirt.util.units import bytes_to_unit

if TYPE_CHECKING:
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
        if not p.match('*.py') or p.match('_*.py'):
            continue

        cmdpath = '.'.join(p.relative_to(SRC_ROOT).with_suffix('').parts)

        assert cmdpath in cmdpaths


def check_mixin(mixin_class: type[ObjectMixin], sample: Entity) -> None:
    '''Sanity check an object mixin class against the specified entity.'''
    mixin = mixin_class()

    assert isinstance(sample, mixin.CLASS)

    for k, v in mixin.DISPLAY_PROPS.items():
        assert isinstance(k, str)
        assert isinstance(v, DisplayProperty)
        assert v.prop in dir(sample)

    for k in mixin.DEFAULT_COLUMNS:
        assert k in mixin.DISPLAY_PROPS.keys()

    for k in mixin.SINGLE_LIST_PROPS:
        assert k in mixin.DISPLAY_PROPS.keys()


def check_list_entry(line: str, obj: Entity, mixin_class: type[ObjectMixin]) -> None:
    '''Check a single entry in the list command output.'''
    mixin = mixin_class()
    cols = [mixin.DISPLAY_PROPS[x] for x in mixin.DEFAULT_COLUMNS]

    values = line.split()

    assert len(values) == len(cols)

    for v, c in zip(values, cols):
        assert v == c.color(getattr(obj, c.prop, None))


def check_list_output(output: str, obj: Entity, mixin_class: type[ObjectMixin]) -> None:
    '''Check that the list command works correctly.'''
    mixin = mixin_class()
    cols = [mixin.DISPLAY_PROPS[x] for x in mixin.DEFAULT_COLUMNS]

    lines = output.splitlines()

    headings = lines[0].split()

    assert len(headings) == len(cols)

    for h, c in zip(headings, cols):
        assert h == c.title

    assert re.match('^-+?$', lines[1])

    check_list_entry(lines[2], obj, mixin_class)


def check_info_output(output: str, entity: Entity, header: str, mixin_class: type[ObjectMixin]) -> None:
    '''Check the output from an info command.'''
    items = mixin_class().DISPLAY_PROPS.values()

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
