# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''libvirt object matching tooling for the fvirt CLI.'''

from __future__ import annotations

import re

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, Type, Any

import click

from lxml import etree

if TYPE_CHECKING:
    from collections.abc import Mapping, Callable

    from .match_alias import MatchAlias
    from ..libvirt.entity import ConfigurableEntity


MATCH_HELP = '''fvirt object matching is based on two parameters passed to the --match
option of a fvirt command. The first is the match target, and the second
is the match pattern.

The match target may be either an XPath expression or a target alias. If
an XPath expression is used, that expression will be evaulated against
the XML configuration of each object to produce the value that will be
matched against. If a target alias is used, then that alias will define
the specific property of the object that will be matched against. In
either case, the value of the property will be converted to a string
using Python’s standard type conversion rules before it is tested
against the pattern.

The match pattern may be any Python regular expression, as supported by the
`re` module in the Python standard library. Capture groups are ignored
in match patterns, but all other features of Python regular expressions
are fully supported.
'''

DEFAULT_MATCH = re.compile('.*')


@dataclass(kw_only=True, slots=True)
class MatchTarget:
    '''Class representing a target for matching.'''
    xpath: etree.XPath | None = None
    property: str | None = None

    def get_value(self: Self, entity: ConfigurableEntity) -> str:
        '''Get the match target value for the specified entity.'''
        if self.xpath is not None:
            result = self.xpath(entity.config)

            if result is None or result == []:
                return ''
            elif isinstance(result, list):
                result = str(result[0])

            return str(result)
        elif self.property is not None:
            if hasattr(entity, self.property):
                ret = getattr(entity, self.property, '')

                if hasattr(ret, '__get__'):
                    ret = ret.__get__(entity)

                return str(ret)
            else:
                return ''
        else:
            return ''


def MatchTargetParam(aliases: Mapping[str, MatchAlias]) -> Type[click.ParamType]:
    '''Factory function for creating types for match tagets.

       This will produce a subclass of click.ParamType for parsing the
       first parameter that should be passed to the `--match` argument
       and converting it to a usable MatchTarget instance, based on the
       mapping of aliases.

       The resultant class can be used with the `type` argument for
       click.option decorators to properly parse match targets for the
       `--match` option.'''
    class MatchTargetParam(click.ParamType):
        name = 'match-target'

        def convert(self: Self, value: str | MatchTarget, param: Any, ctx: click.core.Context | None) -> MatchTarget:
            if isinstance(value, str):
                if value in aliases:
                    ret = MatchTarget(property=aliases[value].property)
                else:
                    ret = MatchTarget(xpath=etree.XPath(value, smart_strings=False))
            else:
                ret = value

            return ret

    return MatchTargetParam


class MatchPatternParam(click.ParamType):
    '''Class for processing match patterns.

       When used as a type for a Click option, this produces a re.Pattern
       object for use with the fvirt.util.match.matcher() function.'''
    name = 'pattern'

    def convert(self: Self, value: str | re.Pattern | None, param: Any, ctx: click.core.Context | None) -> re.Pattern:
        if isinstance(value, str):
            try:
                return re.compile(value)
            except re.error:
                self.fail(f'"{ value }" is not a valid pattern.', param, ctx)
        elif value is None:
            return DEFAULT_MATCH
        else:
            return value


def matcher(target: MatchTarget, pattern: re.Pattern) -> Callable[[ConfigurableEntity], bool]:
    '''Produce a function that checks whether a given entity matches a given target and pattern.

       The produced function is usable with Python’s `filter()`
       builtin and similar functions that need a simple boolean matching
       function.'''
    def match(entity: ConfigurableEntity) -> bool:
        value = target.get_value(entity)
        return pattern.match(value) is not None

    return match


def print_match_help(aliases: Mapping[str, MatchAlias]) -> None:
    '''Handle printing out lists of aliases help info for match options.'''
    click.echo(MATCH_HELP)
    output = 'The following target aliases are recognized in place of an XPath expression for this command:\n'

    for name, alias in aliases.items():
        output += f'  - { name }: { alias.desc }\n'

    click.echo(output)


__all__ = [
    'MatchTarget',
    'MatchTargetParam',
    'MatchPatternParam',
    'matcher',
    'print_match_help',
]