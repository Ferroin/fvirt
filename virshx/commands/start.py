# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start domains.'''

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ..libvirt import Hypervisor
from ..libvirt.domain import MATCH_ALIASES
from ..util.match import MatchTarget, MatchTargetParam, MatchPatternParam, matcher, print_match_help

if TYPE_CHECKING:
    import re


@click.command
@click.option('--match', type=(MatchTargetParam(MATCH_ALIASES)(), MatchPatternParam()),
              help='Limit listed domains by match parameter. For more info, use `--match-help`')
@click.option('--match-help', is_flag=True, default=False,
              help='Show help info about object matching.')
@click.option('--fail-if-no-match', is_flag=True, default=False,
              help='Exit with a failure if no domains are matched.')
@click.argument('domain', nargs=1, required=False)
@click.pass_context
def start(
        ctx: click.core.Context,
        match: tuple[MatchTarget, re.Pattern] | None,
        match_help: bool,
        fail_if_no_match: bool,
        domain: str | None,
        ) -> None:
    '''start (previously defined) inactive domains

       Either a specific domain name to start should be specified as
       DOMAIN, or matching parameters should be specified using the
       --match option, which will then cause all inactive domains that
       match to be started.

       If more than one domain is requested to be started, a failure
       starting any domain will result in a non-zero exit code even if
       some domains were started.'''
    if match_help:
        print_match_help(MATCH_ALIASES)
        ctx.exit(0)

    if match is not None:
        select = matcher(*match)
    elif domain is None:
        click.echo('Either match parameters or a domain name is required.', err=True)
        ctx.exit(1)

    with Hypervisor(hvuri=ctx.obj['uri']) as hv:
        if domain is not None:
            try:
                domains = [hv.domains_by_name[domain]]
            except KeyError:
                click.echo(f'"{ domain }" is not a defined domain on this hypervisor.', err=True)
                ctx.exit(2)
        else:
            domains = list(filter(select, hv.domains))

            if not domains:
                click.echo('No domains found matching the specified criteria.', err=True)
                ctx.exit(2)

        success = 0

        for dom in domains:
            if dom.shutdown():
                click.echo(f'Started domain "{ dom.name }".')
                success += 1
            else:
                click.echo(f'Failed to start domain "{ dom.name }".')

        if success:
            click.echo(f'Successfully started { success } out of { len(domains) } domains.')
        else:
            click.echo('Failed to start any domains.')
            ctx.exit(3)


__all__ = [
    'start',
]
