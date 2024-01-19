# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.commands._base.exitcode'''

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from ruamel.yaml import YAML

from fvirt.commands._base.config import FVirtConfig, get_config
from fvirt.libvirt.exceptions import FVirtException

yaml: Final = YAML()
yaml.representer.add_representer(type(None), lambda r, d: r.represent_scalar('tag:yaml.org,2002:null', 'null'))


def test_get_config_default(isolated_config: None) -> None:
    '''Test the default configuration loaded via get_config.'''
    config = get_config()

    assert isinstance(config, FVirtConfig)
    assert config == FVirtConfig()
    assert config.config_source == 'INTERNAL'


def test_get_config_ignore_config_files(test_configs: None) -> None:
    '''Test the configuration loaded when config files are ignored.'''
    config = get_config(ignore_config_files=True)

    assert isinstance(config, FVirtConfig)
    assert config == FVirtConfig()
    assert config.config_source == 'INTERNAL'


def test_get_config_absolute_path(sample_config: tuple[FVirtConfig, Path], isolated_config: None) -> None:
    '''Test loading a configuration from an absolute path.'''
    saved_conf, conf_path = sample_config

    loaded_config = get_config(conf_path)

    assert isinstance(loaded_config, FVirtConfig)
    assert loaded_config.config_source == str(conf_path)

    loaded_config.config_source = saved_conf.config_source

    assert loaded_config == saved_conf


def test_get_config_no_file(tmp_path: Path, isolated_config: None) -> None:
    '''Test failure of get_config due to the file not existing.'''
    with pytest.raises(FVirtException):
        get_config(tmp_path / 'config.yaml')


def test_get_config_no_parent_directory(tmp_path: Path, isolated_config: None) -> None:
    '''Test failure of get_config due to the path pointing to a nonexistent  directory.'''
    with pytest.raises(FVirtException):
        get_config(tmp_path / 'nonexistent' / 'config.yaml')


def test_get_config_not_a_directory(sample_config: tuple[FVirtConfig, Path], isolated_config: None) -> None:
    '''Test failure of get_config due to the path trying to use a file as a directory.'''
    _, conf_path = sample_config

    with pytest.raises(FVirtException):
        get_config(conf_path / 'config.yaml')


def test_get_config_permission_denied(sample_config: tuple[FVirtConfig, Path], isolated_config: None) -> None:
    '''Test failure of get_config due to invalid permissions.'''
    _, conf_path = sample_config
    conf_path.lchmod(0o040)

    with pytest.raises(FVirtException):
        get_config(conf_path)
