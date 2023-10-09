# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands that apply XSLT documents to objects.'''

from __future__ import annotations

import concurrent.futures

from textwrap import dedent
from typing import TYPE_CHECKING, Self

import click
import libvirt

from lxml import etree

from .match import MatchCommand, get_match_or_entity
from ...libvirt.runner import RunnerResult, run_entity_method, run_sub_entity_method
from ...util.match import MatchAlias, MatchTarget

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
            doc_name: str,
            hvprop: str,
            metavar: str,
            parent_prop: str | None = None,
            parent_name: str | None = None,
            parent_metavar: str | None = None,
            epilog: str | None = None,
            hidden: bool = False,
            deprecated: bool = False,
            ) -> None:
        params: tuple[click.Parameter, ...] = tuple()

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

                if parent is None:
                    futures = [state.pool.submit(
                        run_entity_method,
                        uri=uri,
                        hvprop=hvprop,
                        method='applyXSLT',
                        ident=e.name,  # type: ignore
                        args=[xform],
                    ) for e in get_match_or_entity(
                        hv=hv,
                        hvprop=hvprop,
                        match=match,
                        entity=entity,
                        ctx=ctx,
                        doc_name=doc_name,
                    )]
                else:
                    assert parent_prop is not None

                    parent_obj = getattr(hv, hvprop).get(parent)

                    futures = [state.pool.submit(
                        run_sub_entity_method,
                        uri=uri,
                        hvprop=hvprop,
                        parentprop=parent_prop,
                        method='applyXSLT',
                        ident=(parent_obj.name, e.name),  # type: ignore
                        args=[xform],
                    ) for e in get_match_or_entity(
                        hv=parent_obj,
                        hvprop=parent_prop,
                        match=match,
                        entity=entity,
                        ctx=ctx,
                        doc_name=doc_name,
                    )]

            success = 0

            for f in concurrent.futures.as_completed(futures):
                match f.result():
                    case RunnerResult(attrs_found=False) as r:
                        name = r.ident

                        if parent is not None:
                            name = r.ident[1]

                        ctx.fail(f'Unexpected internal error processing { doc_name } "{ name }".')
                    case RunnerResult(entity_found=False) as r if parent is None:
                        click.echo(f'{ doc_name } "{ r.ident }" disappeared before we could modify it.')

                        if state.fail_fast:
                            break
                    case RunnerResult(entity_found=False) as r:
                        click.echo(f'{ parent_name } "{ r.ident[0] }" not found when trying to modify { doc_name } "{ r.ident[1] }".')
                        break  # Can't recover in this case, but we should still print our normal summary.
                    case RunnerResult(entity_found=True, sub_entity_found=False) as r:
                        click.echo(f'{ doc_name } "{ r.ident[1] }" disappeared before we could modify it.')

                        if state.fail_fast:
                            break
                    case RunnerResult(method_success=False) as r:
                        name = r.ident

                        if parent is not None:
                            name = r.ident[1]

                        click.echo(f'Failed to modify { doc_name } "{ name }".')

                        if state.fail_fast:
                            break
                    case RunnerResult(method_success=True) as r:
                        name = r.ident

                        if parent is not None:
                            name = r.ident[1]

                        click.echo(f'Successfully modified { doc_name } "{ name }".')
                        success += 1
                    case _:
                        raise RuntimeError

            click.echo(f'Finished modifying specified { doc_name }s using XSLT document at { xslt }.')
            click.echo('')
            click.echo('Results:')
            click.echo(f'  Success:     { success }')
            click.echo(f'  Failed:      { len(futures) - success }')
            click.echo(f'Total:         { len(futures) }')

            if success != len(futures) or (not futures and state.fail_if_no_match):
                ctx.exit(3)

        if parent_prop is None:
            docstr = f'''
            Apply an XSLT document to one or more { doc_name }s.

            XSLT must be a path to a valid XSLT document. It must specify an
            output element, and the output element must specify an encoding
            of UTF-8. Note that xsl:strip-space directives may cause issues
            in the XSLT processor.

            Either a specific { doc_name } name to modify should be specified as
            { metavar }, or matching parameters should be specified using the --match
            option, which will then cause all matching { doc_name }s to be modified.

            This command supports fvirt's fail-fast logic. In fail-fast mode,
            the first { doc_name } which the XSLT document fails to apply to will
            cause the operation to stop, and any failure will result in a
            non-zero exit code.

            This command does not support fvirt's idempotent mode. It's
            behavior will not change regardless of whether idempotent mode
            is enabled or not.'''
        else:
            assert parent_name is not None
            assert parent_metavar is not None

            docstr = f'''
            Apply an XSLT document to one or more { doc_name }s in a given { parent_name }.

            XSLT must be a path to a valid XSLT document. It must specify an
            output element, and the output element must specify an encoding
            of UTF-8. Note that xsl:strip-space directives may cause issues
            in the XSLT processor.

            A { parent_name } must be exlicitly specified with the { parent_metavar }
            argument.

            Either a specific { doc_name } name to modify should be specified as
            { metavar }, or matching parameters should be specified using the --match
            option, which will then cause all matching { doc_name }s to be modified.

            This command supports fvirt's fail-fast logic. In fail-fast mode,
            the first { doc_name } which the XSLT document fails to apply to will
            cause the operation to stop, and any failure will result in a
            non-zero exit code.

            This command does not support fvirt's idempotent mode. It's
            behavior will not change regardless of whether idempotent mode
            is enabled or not.'''

            params += (click.Argument(
                param_decls=('parent',),
                metavar=parent_metavar,
                nargs=1,
                required=True,
            ),)

        docstr = dedent(docstr).lstrip()

        params += (
            click.Argument(
                param_decls=('object',),
                nargs=1,
                metavar=metavar,
                required=False,
            ),
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
            doc_name=doc_name,
            params=params,
            hidden=hidden,
            deprecated=deprecated,
        )
