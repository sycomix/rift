"""
Author: E.W.Ayers <contact@edayers.com>
This file is adapted from  https://github.com/EdAyers/sss
"""
import inspect
from typing import Any, Literal, NewType, Optional, Type, Union, get_args, get_origin


def is_optional(T: Type) -> bool:
    """Returns true if ``T == Union[NoneType, _] == Optional[_]``."""
    return as_optional(T) is not None


def as_optional(T: Type) -> Optional[Type]:
    """If we have ``T == Optional[X]``, returns ``X``, otherwise returns ``None``.

    Note that because ``Optional[X] == Union[X, type(None)]``, so
    we have ``as_optional(Optional[Optional[X]]) ↝ X``
    ref: https://stackoverflow.com/questions/56832881/check-if-a-field-is-typing-optional
    """
    if get_origin(T) is Union:
        args = get_args(T)
        if type(None) in args:
            if ts := tuple(a for a in args if a is not type(None)):
                return ts[0] if len(ts) == 1 else Union[ts]
            else:
                return None
    return None


def as_literal(T: Type) -> Optional[tuple[str, ...]]:
    return get_args(T) if get_origin(T) is Literal else None


def as_list(T: Type) -> Optional[Type]:
    """If `T = List[X]`, return `X`, otherwise return None."""
    if T == list:
        return Any
    o = get_origin(T)
    if o is None:
        return None
    return get_args(T)[0] if issubclass(o, list) else None


def as_newtype(T: Type) -> Optional[Type]:
    return getattr(T, "__supertype__", None)


def as_set(T: Type) -> Optional[Type]:
    if T == set:
        return Any
    o = get_origin(T)
    if o is None:
        return None
    return get_args(T)[0] if issubclass(o, set) else None


def is_subtype(T1: Type, T2: Type) -> bool:
    """Polyfill for issubclass.

    Pre 3.10 doesn't have good support for subclassing unions.
    """
    try:
        return issubclass(T1, T2)
    except TypeError:
        if get_origin(T2) is Union:
            return any(is_subtype(T1, a) for a in get_args(T2))
        S = as_newtype(T2)
        if S is not None:
            return is_subtype(T1, S)
        raise
