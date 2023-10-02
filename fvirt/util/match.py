# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''libvirt object matching tooling for the fvirt CLI.'''

from __future__ import annotations

import re

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from lxml import etree

if TYPE_CHECKING:
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

To see a list of recognized match aliases for a given subcommand, run
`fvirt <subcommand> help aliases`
'''

DEFAULT_MATCH = re.compile('.*')


@dataclass(kw_only=True, slots=True)
class MatchAlias:
    '''Class representing the target of a match alias.

       The `property` property is the name of the object property that
       the alias should resolve to the value of.

       The `desc` property should be a short description of what the
       alias matches. It will be included in the output printed by the
       fvirt.util.match.handle_match_parameters() function when the
       user asks for a list of recognized aliases.'''
    property: str
    desc: str


@dataclass(kw_only=True, slots=True)
class MatchTarget:
    '''Class representing a target for matching.

       This encapsulates value lookup logic irrespective of whether the
       target is an xpath specification or a simple property name from
       a match alias.

       If both an xpath and property target are specified, the xpath
       target takes precedence.'''
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


__all__ = [
    'MatchAlias',
    'MatchTarget',
    'MATCH_HELP',
]
