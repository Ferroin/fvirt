# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Command for manipulating autostart status for objects.'''

from __future__ import annotations

import logging

from collections.abc import Sequence
from textwrap import dedent
from typing import TYPE_CHECKING, Final, Self, cast

import click

from .exitcode import ExitCode
from .match import MatchArgument, MatchCommand, get_match_or_entity
from .objects import is_object_mixin
from ...libvirt import InsufficientPrivileges
from ...libvirt.entity import RunnableEntity
from ...util.report import summary

if TYPE_CHECKING:
    from .state import State

LOGGER: Final = logging.getLogger(__name__)


class AutostartCommand(MatchCommand):
    '''Class for commands that manipulate autostart state for objects.

       This provides the callback and all the other info required.'''
    def __init__(
        self: Self,
        name: str,
        epilog: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
    ) -> None:
        assert is_object_mixin(self)

        params = self.mixin_params() + (
            click.Option(
                param_decls=('--enable/--disable',),
                is_flag=True,
                required=True,
            ),
        )

        def cb(ctx: click.Context, state: State, /, match: MatchArgument, entity: str | None, enable: bool) -> None:
            with state.hypervisor as hv:
                entities = cast(Sequence[RunnableEntity], get_match_or_entity(
                    obj=self,
                    hv=hv,
                    match=match,
                    entity=entity,
                    ctx=ctx,
                ))

                success = 0
                skipped = 0

                for e in entities:
                    if e.autostart == enable:
                        skipped += 1
                        if state.idempotent:
                            success += 1
                    else:
                        try:
                            e.autostart = enable
                        except InsufficientPrivileges:
                            LOGGER.error(f'Cannot modify { self.NAME } autostart state as the Hypervisor connection is read-only.')
                            ctx.exit(ExitCode.OPERATION_FAILED)
                        except Exception as e:
                            LOGGER.error('Encountered unexpected error while trying to set autostart status', exc_info=e)
                            ctx.exit(ExitCode.OPERATION_FAILED)

                        success += 1

                click.echo(f'Finished setting autostart status for specified { self.NAME }s.')
                click.echo('')
                click.echo(summary(
                    total=len(entities),
                    success=success,
                    skipped=skipped,
                    idempotent=state.idempotent,
                ))

                if success != len(entities) or (not entities and state.fail_if_no_match):
                    ctx.exit(ExitCode.OPERATION_FAILED)

        docstr = dedent(f'''
        Set autostart state for one or more { self.NAME }s.

        To list the current autostart status for { self.NAME }s, use the
        'list' subcommand.

        Either a specific { self.NAME } to set the autostart state
        for should be specified as NAME, or matching parameters should
        be specified using the --match option, which will then cause
        all active { self.NAME }s that match to have their autostart
        state set.

        If more than one { self.NAME } is requested to have it's
        autostart state set, a failure setting the autostart state for
        any { self.NAME } will result in a non-zero exit code even if
        the autostart state was set successfully for some { self.NAME }s.

        This command does not support parallelization when operating on
        multiple { self.NAME }s. No matter how many jobs are requested,
        only one actual job will be used.

        This command does not support fvirt's fail-fast mode, as the only
        failures possible for this operation will cause the operation
        to fail for all { self.NAME }s.

        This command supports fvirt's idempotent mode. In idempotent mode,
        any { self.NAME }s which already have the desired autostart
        state will be treated as having their state successfully
        set.''').lstrip().rstrip()

        super().__init__(
            name=name,
            callback=cb,
            deprecated=deprecated,
            epilog=epilog,
            help=docstr,
            hidden=hidden,
            params=params,
        )
