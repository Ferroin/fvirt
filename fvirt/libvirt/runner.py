# Copyright (c) 2023 Austin S. Hemmelgarn
# SPDX-License-Identifier: MITNFA

'''Tools for running libvirt operations in other threads or processes.

   These functions are intended to eliminate most of the bolierplate
   code required to sanely handle offloading fvirt.libvirt calls to
   other threads or processes without imposing significant limitations
   on the process.

   Note that these always create a _new_ Hypervisor instance to operate
   on (this is required to support running in other processes), so the
   number of concurrent calls is inherently limited to the number of
   client connections that the target libvirt instance supports.'''

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar, Union
from uuid import UUID

from .entity import Entity
from .events import start_libvirt_event_thread
from .hypervisor import Hypervisor
from .uri import URI

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Mapping, Sequence

I1 = TypeVar('I1', bound=Union[str, int, UUID])
I2 = TypeVar('I2', bound=Union[str, int, UUID])
T1 = TypeVar('T1')
T2 = TypeVar('T2')


@dataclass(kw_only=True, slots=True)
class RunnerResult(Generic[T1, T2]):
    '''Class representing the result of a runner operation.'''
    ident: T1
    attrs_found: bool = True
    entity_found: bool | None = None
    sub_entity_found: bool | None = None
    method_success: bool | None = None
    postproc_success: bool | None = None
    result: T2 | None = None
    exception: Exception | None = None


def _start_event_loop(state: bool | Callable) -> None:
    '''Start the event loop if asked to do so.'''
    match state:
        case True:
            start_libvirt_event_thread()
        case False:
            pass
        case _:
            state()


def _get_entity(parent: Entity | Hypervisor, prop: str, ident: I1, sub_entity: bool = False) -> Entity | RunnerResult[I1, T1 | None]:
    '''Get an entity.'''
    try:
        entity: Entity | None = getattr(parent, prop).get(ident)
    except AttributeError as e:
        if sub_entity:
            return RunnerResult(
                ident=ident,
                attrs_found=False,
                entity_found=True,
                sub_entity_found=False,
                exception=e,
            )
        else:
            return RunnerResult(
                ident=ident,
                attrs_found=False,
                entity_found=False,
                exception=e,
            )

    if entity is None:
        if sub_entity:
            return RunnerResult(
                ident=ident,
                entity_found=True,
                sub_entity_found=False,
            )
        else:
            return RunnerResult(
                ident=ident,
                entity_found=False,
            )

    return entity


def _run_method(
        obj: Entity | Hypervisor,
        method: str,
        ident: T1,
        args: Sequence[Any],
        kwargs: Mapping[str, Any],
        entity: Literal[True] | None = None,
        sub_entity: Literal[True] | None = None
) -> RunnerResult[T1, Any] | Any:
    '''Run a method.'''
    try:
        return getattr(obj, method)(*args, **kwargs)
    except AttributeError as e:
        return RunnerResult(
            ident=ident,
            attrs_found=False,
            entity_found=entity,
            sub_entity_found=sub_entity,
            exception=e,
        )
    except Exception as e:
        return RunnerResult(
            ident=ident,
            method_success=False,
            entity_found=entity,
            sub_entity_found=sub_entity,
            exception=e,
        )


def _set_attribute(
    obj: Entity,
    attrib: str,
    value: Any,
    ident: T1,
    sub_entity: Literal[True] | None = None
) -> RunnerResult[T1, Literal[True] | None]:
    '''Set an attribute.'''
    try:
        setattr(obj, attrib, value)
    except AttributeError as e:
        return RunnerResult(
            ident=ident,
            attrs_found=False,
            entity_found=True,
            sub_entity_found=sub_entity,
            exception=e,
        )
    except Exception as e:
        return RunnerResult(
            ident=ident,
            method_success=False,
            entity_found=True,
            sub_entity_found=sub_entity,
            exception=e,
        )

    return RunnerResult(
        ident=ident,
        method_success=True,
        entity_found=True,
        sub_entity_found=sub_entity,
        result=True,
    )


def _post_process(
        ident: T1,
        result: Any,
        postproc: Callable[[Any], T2],
        entity: Literal[True] | None = None,
        sub_entity: Literal[True] | None = None
) -> RunnerResult[T1, T2]:
    '''Postprocess a result.'''
    try:
        ret = postproc(result)
    except Exception as e:
        return RunnerResult(
            ident=ident,
            method_success=True,
            postproc_success=False,
            entity_found=entity,
            sub_entity_found=sub_entity,
            exception=e,
        )

    return RunnerResult(
        ident=ident,
        method_success=True,
        postproc_success=True,
        entity_found=entity,
        sub_entity_found=sub_entity,
        result=ret,
    )


def run_hv_method(
    uri: URI,
    method: str,
    ident: I1,
    arguments: Sequence[Any],
    kwarguments: Mapping[str, Any],
    postproc: Callable[[Any], T1] = lambda x: x,
    start_event_loop: bool | Callable = False,
) -> RunnerResult[I1, T1]:
    '''Call a Hypervisor method on a new Hypervisor with the given URI.

       The method is called with positional arguments `arguments` and keyword
       arguments `kwarguments`.

       `ident` is an arbitrary value passed in to help identify this
       particular call. It is passed directly through to the returned
       RunnerResult without modification.

       `postproc` is a function that will be used to process the return
       value of the method.

       `start_event_loop` indicates whether or not to start an event loop
       prior to opening the Hypervisor instance. It should be False if
       running in a thread, or True if running in another process. It
       can also be a callable to use to start the event loop.'''
    _start_event_loop(start_event_loop)

    with Hypervisor(hvuri=uri) as hv:
        match _run_method(hv, method, ident, arguments, kwarguments):
            case RunnerResult() as r:
                return r
            case retval:
                ret = retval

        return _post_process(
            ident=ident,
            result=ret,
            postproc=postproc,
        )


def run_entity_method(
    uri: URI,
    hvprop: str,
    method: str,
    ident: I1,
    arguments: Sequence[Any] = [],
    kwarguments: Mapping[str, Any] = dict(),
    postproc: Callable[[Any], T1] = lambda x: x,
    start_event_loop: bool = True
) -> RunnerResult[I1, T1]:
    '''Run a method on an entity in the hypervisor with the specified URI.

       `hvprop` indicates what property on the Hypervisor instance should
       be used to find the entity.

       `ident` will be passed to the `get` method of the hypervisor
       property to look up the target entity.

       The method will be called with positional arguments from `args`
       and keyword arguments from `kwargs`.

       `postproc` is a function that will be used to process the return
       value of the method.

       `start_event_loop` indicates whether or not to start an event loop
       prior to opening the Hypervisor instance. It should be False if
       running in a thread, or True if running in another process.'''
    _start_event_loop(start_event_loop)

    with Hypervisor(hvuri=uri) as hv:
        match _get_entity(hv, hvprop, ident):
            case RunnerResult() as r:
                return r
            case Entity() as e:
                entity = e
            case _:
                raise RuntimeError

        match _run_method(entity, method, ident, arguments, kwarguments, entity=True):
            case RunnerResult() as r:
                return r
            case retval:
                ret = retval

        return _post_process(
            ident=ident,
            result=ret,
            postproc=postproc,
            entity=True,
        )


def run_sub_entity_method(
    uri: URI,
    hvprop: str,
    parentprop: str,
    method: str,
    ident: tuple[I1, I2],
    arguments: Sequence[Any] = [],
    kwarguments: Mapping[str, Any] = dict(),
    postproc: Callable[[Any], T1] = lambda x: x,
    start_event_loop: bool = True
) -> RunnerResult[tuple[I1, I2], T1]:
    '''Run a method on an entity in the hypervisor with the specified URI.

       `hvprop` indicates what property on the Hypervisor instance should
       be used to find the entity.

       `parentprop` indicates what property on the parent entity should
       be used to find the entity.

       `ident` is a 2-tuple containing an identifier to look up the
       parent object, and an identifier to look up the child object.

       The method will be called with positional arguments from `arguments`
       and keyword arguments from `kwarguments`.

       `postproc` is a function that will be used to process the return
       value of the method.

       `start_event_loop` indicates whether or not to start an event loop
       prior to opening the Hypervisor instance. It should be False if
       running in a thread, or True if running in another process.'''
    _start_event_loop(start_event_loop)

    with Hypervisor(hvuri=uri) as hv:
        match _get_entity(hv, hvprop, ident[0]):
            case RunnerResult() as r:
                return r
            case Entity() as e:
                parent = e
            case _:
                raise RuntimeError

        match _get_entity(parent, parentprop, ident[1], sub_entity=True):
            case RunnerResult() as r:
                return r
            case Entity() as e:
                entity = e
            case _:
                raise RuntimeError

        match _run_method(entity, method, ident, arguments, kwarguments, entity=True, sub_entity=True):
            case RunnerResult() as r:
                return r
            case retval:
                ret = retval

        return _post_process(
            ident=ident,
            result=ret,
            postproc=postproc,
            entity=True,
            sub_entity=True,
        )


def set_entity_attribute(
    uri: URI,
    hvprop: str,
    attrib: str,
    value: Any,
    ident: I1,
    start_event_loop: bool = True,
) -> RunnerResult[I1, Literal[True] | None]:
    '''Set an attribute on an entity.

       `hvprop` indicates what property on the Hypervisor instance should
       be used to find the entity.

       `ident` will be passed to the `get` method of the hypervisor
       property to look up the target entity.

       `start_event_loop` indicates whether or not to start an event loop
       prior to opening the Hypervisor instance. It should be False if
       running in a thread, or True if running in another process.'''
    _start_event_loop(start_event_loop)

    with Hypervisor(hvuri=uri) as hv:
        match _get_entity(hv, hvprop, ident):
            case RunnerResult() as r:
                return r
            case Entity() as e:
                entity = e
            case _:
                raise RuntimeError

        return _set_attribute(
            obj=entity,
            attrib=attrib,
            value=value,
            ident=ident,
        )


def set_sub_entity_attribute(
    uri: URI,
    hvprop: str,
    parentprop: str,
    attrib: str,
    value: Any,
    ident: tuple[I1, I2],
    start_event_loop: bool = True,
) -> RunnerResult[tuple[I1, I2], Literal[True] | None]:
    '''Set an attribute on an entity.

       `hvprop` indicates what property on the Hypervisor instance should
       be used to find the entity.

       `parentprop` indicates what property on the parent entity should
       be used to find the entity.

       `ident` is a 2-tuple containing an identifier to look up the
       parent object, and an identifier to look up the child object.

       `start_event_loop` indicates whether or not to start an event loop
       prior to opening the Hypervisor instance. It should be False if
       running in a thread, or True if running in another process.'''
    _start_event_loop(start_event_loop)

    with Hypervisor(hvuri=uri) as hv:
        match _get_entity(hv, hvprop, ident[0]):
            case RunnerResult() as r:
                return r
            case Entity() as e:
                parent = e
            case _:
                raise RuntimeError

        match _get_entity(parent, parentprop, ident[1], sub_entity=True):
            case RunnerResult() as r:
                return r
            case Entity() as e:
                entity = e
            case _:
                raise RuntimeError

        return _set_attribute(
            obj=entity,
            attrib=attrib,
            value=value,
            ident=ident,
        )
