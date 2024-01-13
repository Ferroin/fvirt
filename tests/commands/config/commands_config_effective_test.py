# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.config.effective'''

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Final

from ruamel.yaml import YAML

from fvirt.commands._base.config import FVirtConfig, RuntimeConfig

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from click.testing import Result

yaml: Final = YAML()
yaml.representer.add_representer(type(None), lambda r, d: r.represent_scalar('tag:yaml.org,2002:null', 'null'))


def test_config_effective_command(tmp_path: Path, test_uri: str, runner: Callable[[Sequence[str], int, bool], Result]) -> None:
    '''Test that the config effective command works correctly.'''
    conf: Final = FVirtConfig.model_validate({
        'defaults': {
            'idempotent': True,
            'units': 'si',
            'domain': {
                'default_list_columns': [
                    'name',
                    'uuid',
                ],
            },
            'volume': {
                'default_list_columns': [
                    'name',
                    'path',
                ],
                'sparse_transfer': True,
            },
        },
        'uri': {
            test_uri: {
                'idempotent': False,
                'units': 'iec',
                'pool': {
                    'default_list_columns': [
                        'name',
                        'uuid',
                    ],
                },
                'volume': {
                    'default_list_columns': [
                        'name',
                        'key',
                    ],
                },
            },
        },
    })

    conf_path = tmp_path / 'config.yaml'

    yaml.dump(conf.model_dump(), conf_path)

    result = runner(('-c', test_uri, '--config-file', str(conf_path), 'config', 'effective'), 0, False)

    data = yaml.load(StringIO(result.stdout))

    loaded_conf = RuntimeConfig(data)
    effective_conf = conf.get_effective_config()

    assert loaded_conf == effective_conf
