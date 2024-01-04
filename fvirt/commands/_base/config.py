# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Configuration file handling.'''

from __future__ import annotations

import functools
import logging

from typing import TYPE_CHECKING, Annotated, ClassVar, Final, Literal

from platformdirs import PlatformDirs
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from pathlib import Path

LOGGER: Final = logging.getLogger(__name__)
MODEL_CONFIG: Final = ConfigDict(
    allow_inf_nan=False,
)
DIRS: Final = PlatformDirs('fvirt')
CONFIG_NAMES: Final = (
    'config.yml',
    'config.yaml',
)
CONFIG_PATHS: Final = tuple(
    [DIRS.user_config_path / x for x in CONFIG_NAMES] +
    [DIRS.site_config_path / x for x in CONFIG_NAMES]
)


class LoggingConfig(BaseModel):
    '''Logging configuration for fvirt.'''
    model_config: ClassVar = MODEL_CONFIG

    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = Field(
        default='WARNING',
        description='The log level to use when logging.',
    )
    full_log_output: bool = Field(
        default=False,
        description='If true, produce full logging output on stderr even if running interactively.',
    )


class RuntimeConfig(BaseModel):
    '''Configuration for runtime behavior of fvirt.'''
    model_config: ClassVar = MODEL_CONFIG

    idempotent: bool | None = Field(
        default=None,
        description='Control whether idempotent mode is enabled by default or not.',
    )
    fail_fast: bool | None = Field(
        default=None,
        description='Control whether fail-fast mode is enabled by default or not.',
    )
    fail_if_no_match: bool | None = Field(
        default=None,
        description='Control whether not finding a match with the --match option should be treated as an error by default or not.',
    )
    units: Literal['raw', 'bytes', 'si', 'iec'] | None = Field(
        default=None,
        description='Specify what units to use when displaying large numbers.',
    )
    jobs: Annotated[int, Field(ge=0)] | None = Field(
        default=None,
        description='Specify the default number of jobs to use when executing operations in parallel.',
    )


class FVirtConfig(BaseModel):
    '''Configuration for the fvirt command line tool.'''
    model_config: ClassVar = MODEL_CONFIG

    log: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description='Specifies configuration for logging.',
    )
    defaults: RuntimeConfig = Field(
        default_factory=RuntimeConfig,
        description='Specifies default runtime configuration for fvirt.',
    )
    uris: dict[Annotated[str, Field(min_length=1)], RuntimeConfig] = Field(
        default_factory=dict,
        description='Specifies per-URI overrides for the default runtime configuration.',
    )


@functools.cache
def get_config(config_path: Path | None = None) -> FVirtConfig:
    '''Load the fvirt configuration.'''
    from ruamel.yaml import YAML

    from fvirt.libvirt.exceptions import FVirtException

    yaml = YAML(typ='safe')

    if config_path is not None:
        config_paths: tuple[Path, ...] = (config_path,)
    else:
        config_paths = CONFIG_PATHS

    data = None

    for conf in config_paths:
        LOGGER.debug(f'Checking for configuration at {str(conf)}')
        err = False

        try:
            if conf.is_file():
                LOGGER.info(f'Loading configuration from {str(conf)}')
                data = yaml.load(conf.read_text())
                break
            elif config_path is not None:
                LOGGER.fatal(f'User specified configuration file {str(conf)} could not be found')
                raise FVirtException
        except FileNotFoundError:
            err = True
            msg = 'one or more parent directories do not exist.'
        except NotADirectoryError:
            err = True
            msg = 'one of the parent path components is not a directory.'
        except PermissionError:
            err = True
            msg = 'permission denied.'

        if err:
            if config_path is None:
                LOGGER.info(f'Could not check for {str(conf)}, {msg}')
            else:
                LOGGER.fatal(f'Could not load {str(conf)}, {msg}')
                raise FVirtException

    if data is None:
        LOGGER.info('No configuration file found, using internal defaults.')
        return FVirtConfig()
    else:
        return FVirtConfig.model_validate(data)
