# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Base class used for fvirt commands that apply XSLT documents to objects.'''

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Self, cast

import click
import libvirt

from lxml import etree

from .match import MatchCommand, get_match_or_entity

from ...libvirt import Hypervisor
from ...libvirt.entity import ConfigurableEntity
from ...util.match import MatchAlias, MatchTarget

if TYPE_CHECKING:
    import re

    from collections.abc import Sequence, Mapping


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

        def cb(ctx: click.Context, entity: str | None, match: tuple[MatchTarget, re.Pattern] | None, xslt: str, parent: str | None = None) -> None:
            xform = etree.XSLT(etree.parse(xslt))

            with Hypervisor(hvuri=ctx.obj['uri']) as hv:
                entities = cast(Sequence[ConfigurableEntity], get_match_or_entity(
                    hv=hv,
                    hvprop=hvprop,
                    match=match,
                    entity=entity,
                    ctx=ctx,
                    doc_name=doc_name,
                ))

            success = 0

            for e in entities:
                try:
                    e.applyXSLT(xform)
                except libvirt.libvirtError:
                    click.echo(f'Failed to modify { doc_name } "{ e.name }".')

                    if ctx.obj['fail_fast']:
                        break
                else:
                    click.echo(f'Successfully modified { doc_name } "{ e.name }".')
                    success += 1

            click.echo(f'Finished modifying specified { doc_name }s using XSLT document at { xslt }.')
            click.echo('')
            click.echo('Results:')
            click.echo(f'  Success:     { success }')
            click.echo(f'  Failed:      { len(entities) - success }')
            click.echo(f'Total:         { len(entities) }')

            if success != len(entities) and ctx.obj['fail_fast'] or (not entities and ctx.obj['fail_if_no_match']):
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
