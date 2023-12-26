# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Custom types used by fvirt.libvirt pydantic models.'''

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from ..types import OnOff, Timestamp, YesNo


class Model(BaseModel):
    '''Custom base class for models with modified default config.'''
    model_config: ClassVar = ConfigDict(
        allow_inf_nan=False,
    )


NetPort = Annotated[int, Field(gt=0, lt=65536)]
NonEmptyString = Annotated[str, Field(min_length=1)]
FilePath = Annotated[str, Field(pattern=r'^/.+$')]
FileMode = Annotated[str, Field(pattern=r'^0[0-7]{3}$')]
Hostname = Annotated[str, Field(
    pattern=r'^[a-zA-Z0-9-]{1,63}(\.[a-zA-Z0-9-]{1,63})*\.?$',
    max_length=253,
    json_schema_extra={
        'format': 'hostname',
    },
)]
V_YesNo = Annotated[YesNo, BeforeValidator(lambda v, i: YesNo(v))]
V_OnOff = Annotated[OnOff, BeforeValidator(lambda v, i: OnOff(v))]
V_Timestamp = Annotated[Timestamp, BeforeValidator(lambda v, i: Timestamp(v))]
