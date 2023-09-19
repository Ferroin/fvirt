# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to reset domains.'''

from __future__ import annotations

import re

from collections.abc import Sequence
from typing import cast

import click

from ._common import get_match_or_entity
from ..libvirt import Hypervisor, EntityNotRunning, Domain, LifecycleResult
from ..libvirt.domain import MATCH_ALIASES
from ..util.match import MatchTarget, MatchTargetParam, MatchPatternParam, print_match_help


@click.command
@click.option('--match', type=(MatchTargetParam(MATCH_ALIASES)(), MatchPatternParam()),
              help='Limit domains to operate on by match parameter. For more info, use `--match-help`')
@click.option('--match-help', is_flag=True, default=False,
              help='Show help info about object matching.')
@click.argument('name', nargs=1, required=False)
@click.pass_context
def reset(
        ctx: click.core.Context,
        match: tuple[MatchTarget, re.Pattern] | None,
        match_help: bool,
        name: str | None,
        ) -> None:
    '''Reset one or more running domains.

       Either a specific domain name to reset should be specified as
       NAME, or matching parameters should be specified using the
       --match option, which will then cause all running domains that
       are matched to be reset.

       If more than one domain is requested to be reset, a failure
       resetting any domain will result in a non-zero exit code even if
       some domains were started.

       This command supports virshx's fail-fast logic. In fail-fast mode,
       the first domain that fails to be reset will cause the operation to
       stop, and any failure will result in a non-zero exit code.

       This command does not support virshx's idempotent mode. Behavior
       will be identical no matter whether idempotent mode is enabled
       or not.'''
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
        skipped = 0

        for e in entities:
            try:
                match e.reset():
                    case LifecycleResult.SUCCESS:
                        click.echo(f'Reset domain "{ e.name }".')
                        success += 1
                    case LifecycleResult.FAILURE:
                        click.echo(f'Failed to reset domain "{ e.name }".')

                        if ctx.obj['fail_fast']:
                            break
                    case _:
                        raise RuntimeError
            except EntityNotRunning:
                click.echo(f'Domain "{ e.name }" is not running, and thus cannot be reset.')
                skipped += 1

                if ctx.obj['fail_fast']:
                    break

        if success or (not entities and not ctx.obj['fail_if_no_match']):
            click.echo(f'Successfully reset { success } out of { len(entities) } domains ({ skipped } not running).')

            if success != len(entities) and ctx.obj['fail_fast']:
                ctx.exit(3)
        else:
            click.echo('Failed to reset any domains.')
            ctx.exit(3)


__all__ = [
    'reset',
]
