# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.libvirt.models.storage_pool'''

from __future__ import annotations

import pytest

from pydantic import ValidationError

from fvirt.libvirt.models.storage_pool import PoolFeatures, PoolInfo, PoolSource, PoolTarget

from ...shared import get_test_cases

CASES = get_test_cases('libvirt_models_storage_pool')


@pytest.mark.parametrize('d', CASES['PoolFeatures']['valid'])
def test_PoolFeatures_valid(d: dict) -> None:
    '''Check validation of known-good PoolFeatures dicts.'''
    PoolFeatures.model_validate(d)


@pytest.mark.parametrize('d', CASES['PoolFeatures']['invalid'])
def test_PoolFeatures_invalid(d: dict) -> None:
    '''Check validation of known-bad PoolFeatures dicts.'''
    with pytest.raises(ValidationError):
        PoolFeatures.model_validate(d)


@pytest.mark.parametrize('d', CASES['PoolSource']['valid'])
def test_PoolSource_valid(d: dict) -> None:
    '''Check validation of known-good PoolSource dicts.'''
    PoolSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['PoolSource']['invalid'])
def test_PoolSource_invalid(d: dict) -> None:
    '''Check validation of known-bad PoolSource dicts.'''
    with pytest.raises(ValidationError):
        PoolSource.model_validate(d)


@pytest.mark.parametrize('d', CASES['PoolTarget']['valid'])
def test_PoolTarget_valid(d: dict) -> None:
    '''Check validation of known-good PoolTarget dicts.'''
    PoolTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['PoolTarget']['invalid'])
def test_PoolTarget_invalid(d: dict) -> None:
    '''Check validation of known-bad PoolTarget dicts.'''
    with pytest.raises(ValidationError):
        PoolTarget.model_validate(d)


@pytest.mark.parametrize('d', CASES['PoolInfo']['valid'])
def test_PoolInfo_valid(d: dict) -> None:
    '''Check validation of known-good PoolInfo dicts.'''
    PoolInfo.model_validate(d)


@pytest.mark.parametrize('d', CASES['PoolInfo']['invalid'])
def test_PoolInfo_invalid(d: dict) -> None:
    '''Check validation of known-bad PoolInfo dicts.'''
    with pytest.raises(ValidationError):
        PoolInfo.model_validate(d)
