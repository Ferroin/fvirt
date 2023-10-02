# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''libvirt object matching tooling components that depend on click.'''

from __future__ import annotations

import re

from typing import TYPE_CHECKING, Self, Type, Any

import click

from lxml import etree

from .match import MatchTarget, MatchAlias

if TYPE_CHECKING:
    from collections.abc import Mapping

DEFAULT_MATCH = re.compile('.*')


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


def make_alias_help(aliases: Mapping[str, MatchAlias], group_name: str) -> str:
    '''Construct help text about the recongized aliases.'''
    ret = f''''{ group_name }' subcommands recognize the following match aliases:\n'''

    pad = max([len(x) for x in aliases.keys()]) + 2

    for name, alias in aliases.items():
        ret += click.wrap_text(f'{ name }{ " " * (pad - len(name) - 2) }  { alias.desc }', initial_indent='  ', subsequent_indent=(' ' * (pad + 2)))
        ret += '\n'

    return ret.rstrip()
