# copyright (c) 2023 austin s. hemmelgarn
# spdx-license-identifier: mitnfa

'''Class used to create help commands for fvirt command groups.'''

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

import click

from .command import Command

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from .group import Group
    from ...util.match import MatchAlias


def make_alias_help(aliases: Mapping[str, MatchAlias], group_name: str) -> str:
    '''Construct help text about the recongized match aliases.'''
    ret = f''''{ group_name }' subcommands recognize the following match aliases:\n'''

    pad = max([len(x) for x in aliases.keys()]) + 2

    for name, alias in aliases.items():
        ret += click.wrap_text(f'{ name }{ " " * (pad - len(name) - 2) }  { alias.desc }', initial_indent='  ', subsequent_indent=(' ' * (pad + 2)))
        ret += '\n'

    return ret.rstrip()


@dataclass(kw_only=True, slots=True)
class HelpTopic:
    '''Class representing a supplementary help topic.'''
    name: str
    description: str
    help_text: str


class AliasHelpTopic(HelpTopic):
    '''Special help topic class for info about matching aliases.'''
    def __init__(self: Self, aliases: Mapping[str, MatchAlias], group_name: str, doc_name: str) -> None:
        super().__init__(
            name='aliases',
            description=f'List recognized match aliases for matching { doc_name }s.',
            help_text=make_alias_help(aliases, group_name),
        )


def _print_topics(ctx: click.core.Context, cmds: Mapping[str, click.Command], topics: Iterable[HelpTopic]) -> None:
    '''Print out the topics for a help command.'''
    cmds_width = max([len(x) for x in cmds]) + 2

    click.echo('')
    click.echo('Recognized subcommands:')
    for name, cmd in cmds.items():
        output = f'{ name }{ " " * (cmds_width - len(name) - 2) }  { cmd.get_short_help_str() }'
        click.echo(click.wrap_text(output, initial_indent='  ', subsequent_indent=(' ' * (cmds_width + 2))))

    topics = list(topics)
    topics_width = max([len(x.name) for x in topics]) + 2

    click.echo('')
    click.echo('Additional help topics:')
    for topic in topics:
        output = f'{ topic.name }{ " " * (topics_width - len(topic.name) - 2) }  { topic.description }'
        click.echo(click.wrap_text(output, initial_indent='  ', subsequent_indent=(' ' * (topics_width + 2))))


class HelpCommand(Command):
    '''Class used for constructing help commands for fvirt command groups.

       This handles creation of the actual command callback, as well
       as collation of the list of commands in the group, handling of
       secondary topics, and even setup of arguments.'''
    def __init__(
            self: Self,
            group: Group,
            topics: Iterable[HelpTopic],
            ) -> None:
        topic_map = {t.name: t for t in topics}

        def cb(ctx: click.Context, topic: str | None) -> None:
            match topic:
                case '' | None:
                    ctx.info_name = group.name
                    click.echo(group.get_help(ctx))
                    ctx.exit(0)
                case t if t in topic_map:
                    click.echo(topic_map[t].help_text)
                    ctx.exit(0)
                case t:
                    subcmd = group.get_command(ctx, topic)

                    if subcmd is None:
                        click.echo(f'{ topic } is not a recognized help topic.')
                        _print_topics(ctx, group.commands, topics)
                        ctx.exit(1)
                    else:
                        ctx.info_name = topic
                        click.echo(subcmd.get_help(ctx))
                        if t == 'help':
                            _print_topics(ctx, group.commands, topics)
                        ctx.exit(0)

        super().__init__(
            name='help',
            help=f'''
            Print help for the { group.name } command.

            Without any arguments, prints the high-level help for the command itself.

            With an argument, prints help about that specific subcommand or topic.
            '''.lstrip().rstrip(),
            callback=cb,
            params=[
                click.Argument(
                    param_decls=('topic',),
                    metavar='TOPIC',
                    default='',
                    required=False,
                ),
            ],
        )
