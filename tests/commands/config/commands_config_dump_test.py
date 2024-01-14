# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands.config.dump'''

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Final

from ruamel.yaml import YAML

from fvirt.commands._base.config import FVirtConfig

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from click.testing import Result

yaml: Final = YAML()
yaml.representer.add_representer(type(None), lambda r, d: r.represent_scalar('tag:yaml.org,2002:null', 'null'))


def test_config_dump_default(runner: Callable[[Sequence[str], int, bool], Result], isolated_config: None) -> None:
    '''Test that we correctly dump the default configuration.'''
    result = runner(('config', 'dump'), 0, False)

    data = yaml.load(StringIO(result.stdout))

    config = FVirtConfig.model_validate(data)

    assert config == FVirtConfig()


def test_config_dump_internal(runner: Callable[[Sequence[str], int, bool], Result]) -> None:
    '''Test that we correctly dump the internal configuration.'''
    result = runner(('--ignore-config-files', 'config', 'dump'), 0, False)

    data = yaml.load(StringIO(result.stdout))

    config = FVirtConfig.model_validate(data)

    assert config == FVirtConfig()


def test_config_dump_specific(tmp_path: Path, runner: Callable[[Sequence[str], int, bool], Result]) -> None:
    conf_path = tmp_path / 'config.yaml'

    conf = FVirtConfig()
    conf.log.level = 'DEBUG'
    conf.defaults.idempotent = True

    yaml.dump(conf.model_dump(), conf_path)

    result = runner(('--config-file', str(conf_path), 'config', 'dump'), 0, False)

    data = yaml.load(StringIO(result.stdout))

    loaded_conf = FVirtConfig.model_validate(data)

    assert loaded_conf.config_source == str(conf_path)

    loaded_conf.config_source = conf.config_source

    assert loaded_conf == conf


def test_config_dump_auto(test_config_file: Path, runner: Callable[[Sequence[str], int, bool], Result], test_configs: None) -> None:
    '''Check that dumping a searched config file works correctly.'''
    result = runner(('config', 'dump'), 0, False)

    data = yaml.load(StringIO(result.stdout))
    loaded_conf = FVirtConfig.model_validate(data)

    assert loaded_conf.config_source == str(test_config_file)

    data2 = yaml.load(test_config_file)
    expected_conf = FVirtConfig.model_validate(data2)
    expected_conf.config_source = loaded_conf.config_source

    assert loaded_conf == expected_conf
