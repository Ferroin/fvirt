# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Match alias class for virshx libvirt object matching.

   This is in it’s own module so that virshx.libvirt can import it
   without depending on click, which is required for much of the other
   object matching code.'''

from __future__ import annotations

from dataclasses import dataclass


@dataclass(kw_only=True, slots=True)
class MatchAlias:
    '''Class representing the target of a match alias.

       The `property` property is the name of the object property that
       the alias should resolve to the value of.

       The `desc` property should be a short description of what the
       alias matches. It will be included in the output printed by the
       virshx.util.match.handle_match_parameters() function when the
       user asks for a list of recognized aliases.'''
    property: str
    desc: str


__all__ = [
    'MatchAlias',
]
