# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''A command to reset domains.'''

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

import click

from ...libvirt import Hypervisor, EntityNotRunning, Domain, LifecycleResult
from ...libvirt.domain import MATCH_ALIASES
from ...util.commands import get_match_or_entity, add_match_options

if TYPE_CHECKING:
    import re

    from ...util.match import MatchTarget


@click.command(name='reset')
@add_match_options(MATCH_ALIASES, 'domain')
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

       This command supports fvirt's fail-fast logic. In fail-fast mode,
       the first domain that fails to be reset will cause the operation to
       stop, and any failure will result in a non-zero exit code.

       This command does not support fvirt's idempotent mode. Behavior
       will be identical no matter whether idempotent mode is enabled
       or not.'''
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
