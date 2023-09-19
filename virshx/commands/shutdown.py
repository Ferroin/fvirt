# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to gracefully shut down domains.'''

from __future__ import annotations

import re

from collections.abc import Sequence
from typing import cast

import click

from ._common import get_match_or_entity
from ..libvirt import Hypervisor, EntityNotRunning, TimedOut, Domain
from ..libvirt.domain import MATCH_ALIASES
from ..util.match import MatchTarget, MatchTargetParam, MatchPatternParam, print_match_help


@click.command
@click.option('--match', type=(MatchTargetParam(MATCH_ALIASES)(), MatchPatternParam()),
              help='Limit domains to operate on by match parameter. For more info, use `--match-help`')
@click.option('--match-help', is_flag=True, default=False,
              help='Show help info about object matching.')
@click.option('--timeout', type=click.IntRange(min=0), default=0,
              help='Specify a timeout in seconds within which the domain must shut down. A value of 0 means no timeout.')
@click.option('--force', is_flag=True, default=False,
              help='If a domain fails to shut down within the specified timeout, forcibly stop it.')
@click.argument('name', nargs=1, required=False)
@click.pass_context
def shutdown(
        ctx: click.core.Context,
        match: tuple[MatchTarget, re.Pattern] | None,
        match_help: bool,
        timeout: int,
        force: bool,
        name: str | None,
        ) -> None:
    '''Gracefully shut down one or more running domains.

       Either a specific domain name to reset should be specified as
       NAME, or matching parameters should be specified using the
       --match option, which will then cause all running domains that
       are matched to be reset.

       If more than one domain is requested to be reset, a failure
       resetting any domain will result in a non-zero exit code even if
       some domains were started.

       If a timeout is specified, it is applied for each domain that is
       being shut down. For example, if you use `--match` and it matches
       three domains, and have a timeout of 20 seconds, then it may take
       up to 60 seconds to shut down all the domains.

       This command supports virshx's fail-fast logic. In fail-fast mode,
       the first domain that fails to be reset will cause the operation to
       stop, and any failure will result in a non-zero exit code.

       This command supports virshx's idempotent logic. In idempotent
       mode, failing to shut down a domain because it is not running
       will not be treated as an error.'''
    if match_help:
        print_match_help(MATCH_ALIASES)
        ctx.exit(0)

    with Hypervisor(hvuri=ctx.obj['uri']) as hv:
        entities = cast(Sequence[Domain], get_match_or_entity(
            hv=hv,
            hvprop='domains',
            hvnameprop='domains_by_name',
            match=match,
            entity=name,
            ctx=ctx,
            doc_name='domain',
        ))

        success = 0

        for e in entities:
            try:
                if e.shutdown(timeout=timeout, force=force, idempotent=ctx.obj['idempotent']):
                    click.echo(f'Shut down domain "{ e.name }".')
                    success += 1
                else:
                    click.echo(f'Failed to shut down domain "{ e.name }".')

                    if ctx.obj['fail_fast']:
                        break
            except EntityNotRunning:
                click.echo(f'Domain "{ e.name }" is not running, and thus cannot be shut down.')

                if ctx.obj['fail_fast']:
                    break
            except TimedOut:
                click.echo(f'Timed out while waiting for domain "{ e.name }" to shut down.')

                if ctx.obj['fail_fast']:
                    break

        if success or (not entities and not ctx.obj['fail_if_no_match']):
            click.echo(f'Successfully shut down { success } out of { len(entities) } domains.')

            if success != len(entities) and ctx.obj['fail_fast']:
                ctx.exit(3)
        else:
            click.echo('Failed to shut down any domains.')
            ctx.exit(3)


__all__ = [
    'shutdown',
]
