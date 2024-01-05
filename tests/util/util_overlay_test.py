# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tests for fvirt.util.overlay'''

from __future__ import annotations

from typing import Final

import pytest

from fvirt.util.overlay import Overlay

LAYERS: Final = [
    {
        'a': 1,
        'b': 2,
    },
    {
        'b': 3,
        'c': 4,
    },
    {
        'a': 5,
        'c': 6,
        'd': 7,
    },
]

SIMPLE_OVERLAY: Final = Overlay(*LAYERS)
COMPLEX_OVERLAY: Final = Overlay(*[
    {'map': x} for x in LAYERS
])


def test_overlay_layers() -> None:
    '''Check that the layers property works correctly.'''
    for idx in range(0, len(SIMPLE_OVERLAY.layers)):
        assert SIMPLE_OVERLAY.layers[idx] == LAYERS[idx]


def test_overlay_lookup() -> None:
    '''Test simple key lookups for an overlay.'''
    assert SIMPLE_OVERLAY['a'] == LAYERS[0]['a']
    assert SIMPLE_OVERLAY['b'] == LAYERS[0]['b']
    assert SIMPLE_OVERLAY['c'] == LAYERS[1]['c']
    assert SIMPLE_OVERLAY['d'] == LAYERS[2]['d']

    with pytest.raises(KeyError):
        SIMPLE_OVERLAY['z']


def test_overlay_get() -> None:
    '''Check that the Overlay.get() method works correctly.'''
    assert SIMPLE_OVERLAY.get('a') == LAYERS[0].get('a')
    assert SIMPLE_OVERLAY.get('b') == LAYERS[0].get('b')
    assert SIMPLE_OVERLAY.get('c') == LAYERS[1].get('c')
    assert SIMPLE_OVERLAY.get('d') == LAYERS[2].get('d')

    assert SIMPLE_OVERLAY.get('z') is None


def test_overlay_len() -> None:
    '''Check that len() works correctly for overlays.'''
    assert len(SIMPLE_OVERLAY) == len(set().union(*[set(x) for x in LAYERS]))


def test_overlay_to_dict() -> None:
    '''Check that the Overlay.to_dict() method works correctly.'''
    assert SIMPLE_OVERLAY.to_dict() == {
        'a': 1,
        'b': 2,
        'c': 4,
        'd': 7,
    }


def test_overlay_sub_map() -> None:
    '''Check that mapping values are returned as Ovelrays.'''
    assert COMPLEX_OVERLAY['map'] == SIMPLE_OVERLAY
