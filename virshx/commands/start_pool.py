# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to start storage pools.'''

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ..libvirt import Hypervisor
from ..libvirt.storage_pool import MATCH_ALIASES
from ..util.match import MatchTarget, MatchTargetParam, MatchPatternParam, matcher, print_match_help

if TYPE_CHECKING:
    import re


@click.command
@click.option('--match', type=(MatchTargetParam(MATCH_ALIASES)(), MatchPatternParam()),
              help='Limit listed pools by match parameter. For more info, use `--match-help`')
@click.option('--match-help', is_flag=True, default=False,
              help='Show help info about object matching.')
@click.option('--fail-if-no-match', is_flag=True, default=False,
              help='Exit with a failure if no storage pools are matched.')
@click.argument('pool', nargs=1, required=False)
@click.pass_context
def start_pool(
        ctx: click.core.Context,
        match: tuple[MatchTarget, re.Pattern] | None,
        match_help: bool,
        fail_if_no_match: bool,
        pool: str | None,
        ) -> None:
    '''Start (previously defined) inactive storage pools.

       Either a specific storage pool name to start should be specified
       as POOL, or matching parameters should be specified using the
       --match option, which will then cause all inactive storage pools
       that match to be started.

       If more than one storage pool is requested to be started, a
       failure starting any storage pool will result in a non-zero exit
       code even if some storage pools were started.

       This command supports virshx's fail-fast logic. In fail-fast mode,
       the first storage pool that fails to start will cause the operation
       to stop, and any failure will result in a non-zero exit code.

       This command supports virshx's idempotent logic. In idempotent
       mode, failing to start a storage pool because it is already
       running will not be treated as an error.'''
    if match_help:
        print_match_help(MATCH_ALIASES)
        ctx.exit(0)

    if match is not None:
        select = matcher(*match)
    elif pool is None:
        click.echo('Either match parameters or a storage pool name is required.', err=True)
        ctx.exit(1)

    with Hypervisor(hvuri=ctx.obj['uri']) as hv:
        if pool is not None:
            try:
                pools = [hv.pools_by_name[pool]]
            except KeyError:
                click.echo(f'"{ pool }" is not a defined storage pool on this hypervisor.', err=True)
                ctx.exit(2)
        else:
            pools = list(filter(select, hv.pools))

            if not pools and fail_if_no_match:
                click.echo('No storage pools found matching the specified criteria.', err=True)
                ctx.exit(2)

        success = 0

        for entity in pools:
            if entity.start(idempotent=ctx.obj['idempotent']):
                click.echo(f'Started storage pool "{ entity.name }".')
                success += 1
            else:
                if entity.running:
                    click.echo(f'Storage pool "{ entity.name }" is already running.')
                else:
                    click.echo(f'Failed to start storage pool "{ entity.name }".')

                if ctx.obj['fail_fast']:
                    break

        if success or (not pools and not fail_if_no_match):
            click.echo(f'Successfully started { success } out of { len(pools) } storage pools.')
        else:
            click.echo('Failed to start any storage pools.')
            ctx.exit(3)


__all__ = [
    'start_pool',
]
