# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.models.volume'''

from __future__ import annotations

import pytest

from pydantic import ValidationError

from fvirt.libvirt.models.volume import VolumeInfo

from ...shared import get_test_cases

CASES = get_test_cases('libvirt_models_volume')


@pytest.mark.parametrize('d', CASES['VolumeInfo']['valid'])
def test_VolumeInfo_valid(d: dict) -> None:
    '''Check validation of known-good VolumeInfo dicts.'''
    VolumeInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['VolumeInfo']['invalid'])
def test_VolumeInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad VolumeInfo dicts.'''
    with pytest.raises(ValidationError):
        VolumeInfo.model_validate(d)
