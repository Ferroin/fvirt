# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Custom types used by fvirt.libvirt pydantic models.'''

from __future__ import annotations

from typing import Any, ClassVar, Self, Type

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


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

    def __init__(self: Self, value: Any) -> None:
        if not self.TRUE_STR or not self.FALSE_STR:
            raise NotImplementedError

        if value == self.TRUE_STR:
            self.__value = True
        elif value == self.FALSE_STR:
            self.__value = False
        else:
            self.__value = bool(value)

    def __hash__(self: Self) -> int:
        return hash(self.__value)

    def __bool__(self: Self) -> bool:
        return self.__value

    def __str__(self: Self) -> str:
        if self.__value:
            return self.TRUE_STR

        return self.FALSE_STR

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
            python_schema=core_schema.union_schema(
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
                    core_schema.is_subclass_schema(
                        cls=CustomBool,
                    ),
                ],
            ),
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


class OnOff(CustomBool):
    '''A boolean that is represented in XML as either 'on' or 'off'.'''
    TRUE_STR = 'on'
    FALSE_STR = 'off'
