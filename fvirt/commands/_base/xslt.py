# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands that apply XSLT documents to objects.'''

from __future__ import annotations

import concurrent.futures

from textwrap import dedent
from typing import TYPE_CHECKING, Self

import click

from lxml import etree

from .match import MatchCommand, get_match_or_entity
from .objects import is_object_mixin
from ...libvirt.runner import RunnerResult, run_entity_method, run_sub_entity_method
from ...util.match import MatchAlias, MatchTarget
from ...util.report import summary

if TYPE_CHECKING:
    import re

    from collections.abc import Mapping

    from .state import State


class XSLTCommand(MatchCommand):
    '''Command class for applying XSLT documents to objects.

       This handles the required callback, as well as all the required
       options and generation of the help text.'''
    def __init__(
            self: Self,
            name: str,
            aliases: Mapping[str, MatchAlias],
            epilog: str | None = None,
            hidden: bool = False,
            deprecated: bool = False,
    ) -> None:
        assert is_object_mixin(self)

        def cb(
                ctx: click.Context,
                state: State,
                entity: str | None,
                match: tuple[MatchTarget, re.Pattern] | None,
                xslt: str,
                parent: str | None = None
        ) -> None:
            xform = etree.XSLT(etree.parse(xslt))

            with state.hypervisor as hv:
                uri = hv.uri

                if self.HAS_PARENT:
                    assert self.PARENT_ATTR is not None

                    parent_obj = self.get_parent_obj(ctx, hv, parent)

                    futures = [state.pool.submit(
                        run_sub_entity_method,
                        uri=uri,
                        hvprop=self.PARENT_ATTR,
                        parentprop=self.LOOKUP_ATTR,
                        method='apply_xslt',
                        ident=(parent_obj.name, e.name),
                        arguments=[xform],
                    ) for e in get_match_or_entity(
                        hv=hv,
                        obj=self,
                        match=match,
                        entity=entity,
                        ctx=ctx,
                    )]
                else:
                    futures = [state.pool.submit(
                        run_entity_method,  # type: ignore
                        uri=uri,
                        hvprop=self.LOOKUP_ATTR,
                        method='apply_xslt',
                        ident=e.name,
                        arguments=[xform],
                    ) for e in get_match_or_entity(
                        hv=hv,
                        obj=self,
                        match=match,
                        entity=entity,
                        ctx=ctx,
                    )]

            success = 0

            for f in concurrent.futures.as_completed(futures):
                match f.result():
                    case RunnerResult(attrs_found=False) as r:
                        name = r.ident

                        if parent is not None:
                            name = r.ident[1]

                        ctx.fail(f'Unexpected internal error processing { self.NAME } "{ name }".')
                    case RunnerResult(entity_found=False) as r if parent is None:
                        click.echo(f'{ self.NAME } "{ r.ident }" disappeared before we could modify it.')

                        if state.fail_fast:
                            break
                    case RunnerResult(entity_found=False) as r:
                        click.echo(f'{ self.PARENT_NAME } "{ r.ident[0] }" not found when trying to modify { self.NAME } "{ r.ident[1] }".')
                        break  # Can't recover in this case, but we should still print our normal summary.
                    case RunnerResult(entity_found=True, sub_entity_found=False) as r:
                        click.echo(f'{ self.NAME } "{ r.ident[1] }" disappeared before we could modify it.')

                        if state.fail_fast:
                            break
                    case RunnerResult(method_success=False) as r:
                        name = r.ident

                        if parent is not None:
                            name = r.ident[1]

                        click.echo(f'Failed to modify { self.NAME } "{ name }".')

                        if state.fail_fast:
                            break
                    case RunnerResult(method_success=True) as r:
                        name = r.ident

                        if parent is not None:
                            name = r.ident[1]

                        click.echo(f'Successfully modified { self.NAME } "{ name }".')
                        success += 1
                    case _:
                        raise RuntimeError

            click.echo(f'Finished modifying specified { self.NAME }s using XSLT document at { xslt }.')
            click.echo('')
            click.echo(summary(
                total=len(futures),
                success=success,
            ))

            if success != len(futures) or (not futures and state.fail_if_no_match):
                ctx.exit(3)

        if self.HAS_PARENT:
            header = f'Apply an XSLT document to one or more { self.NAME }s.'
        else:
            header = f'''
            Apply an XSLT document to one or more { self.NAME }s in a given { self.PARENT_NAME }.

            A { self.PARENT_NAME } must be exlicitly specified with the { self.PARENT_METAVAR }
            argument.
            '''

        body = f'''
        Either a specific { self.NAME } name to modify should be specified as
        { self.METAVAR }, or matching parameters should be specified using the --match
        option, which will then cause all matching { self.NAME }s to be modified.

        XSLT must be a path to a valid XSLT document. It must specify an
        output element, and the output element must specify an encoding
        of UTF-8. Note that xsl:strip-space directives may cause issues
        in the XSLT processor.

        This command supports fvirt's fail-fast logic. In fail-fast mode,
        the first { self.NAME } which the XSLT document fails to apply to will
        cause the operation to stop, and any failure will result in a
        non-zero exit code.

        This command does not support fvirt's idempotent mode. It's
        behavior will not change regardless of whether idempotent mode
        is enabled or not.'''

        docstr = dedent(f'{ header }\n{ body }').lstrip()

        params = self.mixin_params() + (
            click.Argument(
                param_decls=('xslt',),
                nargs=1,
                type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True),
                required=True,
            ),
        )

        super().__init__(
            name=name,
            help=docstr,
            aliases=aliases,
            epilog=epilog,
            callback=cb,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )
