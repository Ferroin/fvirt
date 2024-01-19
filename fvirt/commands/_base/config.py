# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Configuration file handling.'''

from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Final, Literal, Self, TypeVar

from platformdirs import PlatformDirs
from pydantic import BaseModel, ConfigDict, Field

from ..domain._mixin import _DISPLAY_PROPERTIES as DOMAIN_DISPLAY_PROPS
from ..pool._mixin import _DISPLAY_PROPERTIES as POOL_DISPLAY_PROPS
from ..volume._mixin import _DISPLAY_PROPERTIES as VOLUME_DISPLAY_PROPS
from ...util.overlay import Overlay

if TYPE_CHECKING:
    from pathlib import Path

    from ...libvirt.uri import LIBVIRT_URI

LOGGER: Final = logging.getLogger(__name__)
MODEL_CONFIG: Final = ConfigDict(
    allow_inf_nan=False,
)
DIRS: Final = PlatformDirs('fvirt')
CONFIG_NAMES: Final = (
    'config.yml',
    'config.yaml',
)
CONFIG_PATHS = tuple(
    [DIRS.user_config_path / x for x in CONFIG_NAMES] +
    [DIRS.site_config_path / x for x in CONFIG_NAMES]
)
T = TypeVar('T')


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


class DomainConfig(BaseModel):
    '''Configuration for domain sub-commands.'''
    model_config: ClassVar = MODEL_CONFIG

    default_list_columns: list[Annotated[str, Field(pattern=f'^({"|".join(DOMAIN_DISPLAY_PROPS.keys())})$')]] | None = Field(
        default=None,
        description='Specifies the default to use for domain list commands. If empty, the internal default is used.',
    )


class PoolConfig(BaseModel):
    '''Configuration for pool sub-commands.'''
    model_config: ClassVar = MODEL_CONFIG

    default_list_columns: list[Annotated[str, Field(pattern=f'^({"|".join(POOL_DISPLAY_PROPS.keys())})$')]] | None = Field(
        default=None,
        description='Specifies the default columns to use for pool list commands. If empty, the internal default is used.',
    )


class VolumeConfig(BaseModel):
    '''Configuration for volume sub-commands.'''
    model_config: ClassVar = MODEL_CONFIG

    default_list_columns: list[Annotated[str, Field(pattern=f'^({"|".join(VOLUME_DISPLAY_PROPS.keys())})$')]] | None = Field(
        default=None,
        description='Specifies the default columns to use for volume list commands. If empty, the internal default is used.',
    )
    sparse_transfer: bool | None = Field(
        default=None,
        description='Specifies whether to use sparse mode by default when uploading or aodnloading a volume. If empty, the internal default is used.',
    )


ConfigSection = DomainConfig | PoolConfig | VolumeConfig


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
    domain: DomainConfig = Field(
        default_factory=DomainConfig,
        description='Configuration for domain sub-commands.',
    )
    pool: PoolConfig = Field(
        default_factory=PoolConfig,
        description='Configuration for pool sub-commands.',
    )
    volume: VolumeConfig = Field(
        default_factory=VolumeConfig,
        description='Configuration for volume sub-commands.',
    )


class FVirtConfig(BaseModel):
    '''Configuration for the fvirt command line tool.'''
    model_config: ClassVar = MODEL_CONFIG

    config_source: str = Field(
        default='INTERNAL',
        description='Overridden automatically to indicate what configuration file was used. Ignored on input.',
    )
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

    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._effective: dict[LIBVIRT_URI, RuntimeConfig] = dict()

    def get_effective_config(self: Self, uri: LIBVIRT_URI) -> RuntimeConfig:
        if uri not in self._effective:
            self._effective[uri] = RuntimeConfig(**Overlay(
                self.uris.get(str(uri), RuntimeConfig()).model_dump(),
                self.defaults.model_dump(),
            ))

        return self._effective[uri]


def get_config(config_path: Path | None = None, ignore_config_files: bool = False) -> FVirtConfig:
    '''Load the fvirt configuration.'''
    if ignore_config_files:
        LOGGER.info('Ignoring external configuration, using internal defaults.')
        return FVirtConfig()

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
                data['config_source'] = str(conf)
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
