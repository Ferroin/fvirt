# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Custom types used by fvirt.libvirt pydantic models.'''

from __future__ import annotations

import datetime
import math

from typing import Annotated, Any, ClassVar, Final, Self, Type

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, GetCoreSchemaHandler
from pydantic_core import core_schema

ISO_8601_PATTERN: Final = r'^\d{4}-(\d{2}-\d{2}|W\d{2}-\d)[T ][0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$'


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


class CustomBool:
    '''Boolean represented in libvirt XML by specific string values.

       Values are represented in XML by strings specified by the class
       variables TRUE_STR and FALSE_STR.

       Instantiation expects one of these string values to indicate
       the value. If the value is not one of these values, it will be
       converted to a boolean and that will be used to set the value.

       Conversion to a string will produce these values.

       Conversion to a bool will produce an appropriate boolean value.

       Values are case sensitive.

       This class provides the required machinery to be used with Pydantic.'''
    TRUE_STR: ClassVar[str] = ''
    FALSE_STR: ClassVar[str] = ''
    __slots__ = (
        '__value',
    )

    def __init__(self: Self, value: bool | str | CustomBool) -> None:
        if not self.TRUE_STR or not self.FALSE_STR:
            raise NotImplementedError

        match value:
            case bool():
                self.__value = value
            case CustomBool():
                self.__value = bool(value)
            case self.TRUE_STR:
                self.__value = True
            case self.FALSE_STR:
                self.__value = False
            case _:
                raise ValueError(value)

    def __hash__(self: Self) -> int:
        return hash(self.__value)

    def __bool__(self: Self) -> bool:
        return self.__value

    def __str__(self: Self) -> str:
        if self.__value:
            return self.TRUE_STR

        return self.FALSE_STR

    def __eq__(self: Self, other: Any) -> bool:
        match other:
            case bool():
                return bool(self) == other
            case str():
                return str(self) == other
            case CustomBool():
                return bool(self) == bool(other)
            case _:
                return False

    @classmethod
    def __get_pydantic_core_schema__(
        cls: Type[Self],
        source: Type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        assert source is cls

        return core_schema.json_or_python_schema(
            json_schema=core_schema.union_schema(
                [
                    core_schema.literal_schema(
                        expected=[
                            cls.TRUE_STR,
                            cls.FALSE_STR,
                        ],
                    ),
                    core_schema.bool_schema(
                        strict=True,
                    ),
                ],
            ),
            python_schema=core_schema.is_instance_schema(source),
            serialization=core_schema.plain_serializer_function_ser_schema(
                bool,
                info_arg=False,
                return_schema=core_schema.bool_schema(),
                when_used='json-unless-none',
            ),
        )


class YesNo(CustomBool):
    '''A boolean that is represented in XML as either 'yes' or 'no'.'''
    TRUE_STR = 'yes'
    FALSE_STR = 'no'


V_YesNo = Annotated[YesNo, BeforeValidator(lambda v, i: YesNo(v))]


class OnOff(CustomBool):
    '''A boolean that is represented in XML as either 'on' or 'off'.'''
    TRUE_STR = 'on'
    FALSE_STR = 'off'


V_OnOff = Annotated[OnOff, BeforeValidator(lambda v, i: OnOff(v))]


class Timestamp:
    '''Custom timestamp class that provides direct formatting for use with libvirt XML.

       The constructor takes either an string consisting of
       an ISO 8601 timestamp that would be accepted by Python's
       datetime.datetime.fromisoformat() method, an integral number
       of seconds since the epoch in UTC, an existing Python
       datetime.datetime instance, or an existing datetime.date instance
       (in which case the time will be set to midnight UTC on that day).

       The timestamp is internally normalized to UTC, and all output
       will utilize the UTC time it represents (this is required by a
       number of things in libvirt domain XML). Note that this handles
       naive datetime.datetime instnaces just like the underlying Python
       standard library does, so it is strongly recommended to use aware
       datetime.datetime instances.

       Converting to an integer will produce an integral number of
       seconds since the epoch in UTC, truncating any microseconds.

       Converting to a float will also give the number of seconds since
       the epoch in UTC, but microseconds will be converted to fractional
       seconds.

       Converting to a string will produce an ISO 8601-compliant timestamp
       _without a timezone_, representing the time in UTC.

       This class provides the required machinery to be used with Pydantic.'''
    __slots__ = (
        '__value',
    )

    def __init__(self: Self, tstamp: int | str | datetime.datetime | datetime.date = datetime.datetime.now()) -> None:
        match tstamp:
            case int():
                self.__value = datetime.datetime.fromtimestamp(tstamp, datetime.timezone.utc)
            case str():
                self.__value = datetime.datetime.fromisoformat(tstamp)

                if self.__value.tzinfo is None:
                    self.__value = datetime.datetime(
                        year=self.__value.year,
                        month=self.__value.month,
                        day=self.__value.day,
                        hour=self.__value.hour,
                        minute=self.__value.minute,
                        second=self.__value.second,
                        microsecond=self.__value.microsecond,
                        fold=self.__value.fold,
                        tzinfo=datetime.timezone.utc,
                    )
            case datetime.datetime():
                self.__value = datetime.datetime.astimezone(tstamp, datetime.timezone.utc)
            case datetime.date():
                self.__value = datetime.datetime(
                    year=tstamp.year,
                    month=tstamp.month,
                    day=tstamp.day,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                    fold=0,
                    tzinfo=datetime.timezone.utc,
                )
            case _:
                raise ValueError

    def __int__(self: Self) -> int:
        return math.trunc(self.__value.timestamp())

    def __float__(self: Self) -> float:
        return self.__value.timestamp()

    def __str__(self: Self) -> str:
        return self.__value.strftime('%Y-%m-%dT%H:%M:%S')

    @classmethod
    def __get_pydantic_core_schema__(
        cls: Type[Self],
        source: Type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        assert source is cls

        return core_schema.json_or_python_schema(
            json_schema=core_schema.union_schema(
                [
                    core_schema.str_schema(
                        pattern=ISO_8601_PATTERN,
                        strict=True,
                    ),
                    core_schema.int_schema(
                        strict=True,
                    ),
                ],
            ),
            python_schema=core_schema.is_instance_schema(Timestamp),
            serialization=core_schema.to_string_ser_schema(
                when_used='json-unless-none',
            ),
        )


V_Timestamp = Annotated[Timestamp, BeforeValidator(lambda v, i: Timestamp(v))]
