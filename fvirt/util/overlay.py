# Copyright (c) 2024 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Mapping that auto-merges two other mappings.'''

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Self, TypeVar, cast

K = TypeVar('K')
V = TypeVar('V')


class Overlay(Mapping[K, V]):
    '''An immutable mapping that presents a merged view of multiple other mappings.

       When looking up the value of a key in an Overlay, the layers are
       searched in the order they were passed to the constructor, and
       only if none of them has the requested key is a KeyError returned.

       Values are looked up on-demand, meaning that overlays are more time
       and space efficient than fully merging the underlying layers when dealing
       with large mappings where only a few keys need to be accessed.

       Modifications to the underlying mappings will be visible through
       the overlay.

       An Overlay will automatically handle recursion into other mappings,
       if a value that an Overlay would return would be a mapping,
       another Overlay will be returned instead, merging the mappings
       in each of the underlying layers.

       Overlays will not recurse into or merge sequences.

       The order of keys returned by the keys() method or iteration is
       not guaranteed to correlate in any way with the ordering of keys
       within the underlying mappings.'''
    __slots__ = (
        '_layers',
    )

    def __init__(self: Self, *layers: Mapping[K, V]) -> None:
        self._layers = tuple(layers)

    def __getitem__(self: Self, key: K) -> V | Overlay:  # type: ignore
        found = False

        for layer in self._layers:
            if key in layer:
                v = layer[key]
                found = True
                break

        if not found:
            raise KeyError

        if isinstance(v, Mapping):
            child_layers = []

            for layer in self._layers:
                if key in layer:
                    if isinstance(layer[key], Mapping):
                        child_layers.append(layer[key])

            v = Overlay(*child_layers)  # type: ignore

        return v

    def __iter__(self: Self) -> Iterator[K]:
        return iter(set().union(*[set(x) for x in self._layers]))

    def __len__(self: Self) -> int:
        return len(set().union(*[set(x) for x in self._layers]))

    @property
    def layers(self: Self) -> tuple[Mapping[K, V], ...]:
        return self._layers

    def to_dict(self: Self) -> dict[K, V]:
        '''Recursively convert the overlay to a dictionary.

           This is preferred to simply passing an overlay to the builtin
           dict() function, because it ensures that any values that are
           themselves mappings get converted to dicts also.'''
        ret: dict[K, V] = {}

        for k, v in self.items():
            if isinstance(v, Overlay):
                ret[k] = cast(V, v.to_dict())
            else:
                ret[k] = v

        return ret
