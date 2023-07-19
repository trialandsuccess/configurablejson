import json.encoder as e
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Optional,
    Protocol,
    Type,
    TypeVar,
)

try:
    from _json import encode_basestring, encode_basestring_ascii  # type: ignore
except ImportError:
    encode_basestring_ascii = e.py_encode_basestring_ascii
    encode_basestring = e.py_encode_basestring

if TYPE_CHECKING:
    from .encode import JSONRule

__all__ = ["_make_iterencode", "encode_basestring_ascii", "encode_basestring", "ReprMethod"]

ReprMethod = Callable[..., str]


class FloatstrMethod(Protocol):
    def __call__(
        self,
        o: Any,
        allow_nan: bool = False,
        _repr: ReprMethod = float.__repr__,
        _inf: float = float("inf"),
        _neginf: float = -float("inf"),
    ) -> str:
        ...


IterencodeGenerator = Generator[str, None, None]
Iterencode = Callable[[Any, int], IterencodeGenerator]

K = TypeVar("K")
V = TypeVar("V")

Int = int
T_int = type[Int]
Float = float
T_float = Type[Float]
Str = str
T_str = Type[Str]
Tuple = tuple[Any, ...]
T_tuple = type[Tuple]
List = list[Any]
T_list = type[List]
Dict = dict[K, V]
T_dict = type[Dict[K, V]]


def _make_iterencode(
    rule_cb: Callable[..., "JSONRule"],
    markers: Optional[dict[int, Any]],
    _default: Callable[[Any], dict[str, Any] | list[Any] | str],
    _encoder: Callable[[str], str],
    _indent: Int | Str,
    _floatstr: FloatstrMethod,
    _key_separator: str,
    _item_separator: str,
    _sort_keys: bool,
    _skipkeys: bool,
    _one_shot: bool,
    ## HACK: hand-optimized bytecode; turn globals into locals
    ValueError: type[Exception] = ValueError,  # noqa: A002
    dict: T_dict[Any, Any] = dict,  # noqa: A002
    float: T_float = float,  # noqa: A002
    id: Callable[[Any], int] = id,  # noqa: A002
    int: T_int = int,  # noqa: A002
    isinstance: Callable[[Any, type | tuple[type, ...]], bool] = isinstance,  # noqa: A002
    list: T_list = list,  # noqa: A002
    str: T_str = str,  # noqa: A002
    tuple: T_tuple = tuple,  # noqa: A002
    _intstr: Callable[[Any], str] = int.__repr__,
) -> Iterencode:
    """
    Stolen from json.encoder and changed.
    """
    if _indent is not None and not isinstance(_indent, str):
        indent_str = " " * _indent  # type: ignore
    else:
        indent_str: str = _indent  # type: ignore

    def _iterencode_list(
        lst: List,
        _current_indent_level: Int,
    ) -> IterencodeGenerator:
        if not lst:
            yield "[]"
            return
        if markers is not None:
            markerid = id(lst)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        buf = "["
        if indent_str is not None:
            _current_indent_level += 1
            newline_indent = "\n" + indent_str * _current_indent_level
            separator = _item_separator + newline_indent
            buf += newline_indent
        else:
            newline_indent = None
            separator = _item_separator
        first = True
        for value in lst:
            if first:
                first = False
            else:
                buf = separator

            # CHANGED FROM HERE:
            extra_rule: JSONRule = rule_cb(value, with_default=False)

            if extra_rule and extra_rule.preprocess:
                value = extra_rule.preprocess(value)

            if extra_rule and extra_rule.transform:
                yield buf + extra_rule.transform(value)
            # / TO HERE

            elif isinstance(value, str):
                yield buf + _encoder(value)
            elif value is None:
                yield buf + "null"
            elif value is True:
                yield buf + "true"
            elif value is False:
                yield buf + "false"
            elif isinstance(value, int):
                # Subclasses of int/float may override __repr__, but we still
                # want to encode them as integers/floats in JSON. One example
                # within the standard library is IntEnum.
                yield buf + _intstr(value)
            elif isinstance(value, float):
                # see comment above for int
                yield buf + _floatstr(value)
            else:
                yield buf
                if isinstance(value, (list, tuple)):
                    chunks = _iterencode_list(value, _current_indent_level)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, _current_indent_level)
                else:
                    chunks = _iterencode(value, _current_indent_level)
                yield from chunks
        if newline_indent is not None:
            _current_indent_level -= 1
            yield "\n" + indent_str * _current_indent_level
        yield "]"
        if markers is not None:
            del markers[markerid]

    def _iterencode_dict(dct: Dict[Any, Any], _current_indent_level: Int) -> IterencodeGenerator:
        if not dct:
            yield "{}"
            return
        if markers is not None:
            markerid = id(dct)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = dct
        yield "{"
        if indent_str is not None:
            _current_indent_level += 1
            newline_indent = "\n" + indent_str * _current_indent_level
            item_separator = _item_separator + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = _item_separator
        first = True

        items = sorted(dct.items()) if _sort_keys else dct.items()

        for key, value in items:
            # CHANGED FROM HERE:
            extra_rule: JSONRule = rule_cb(key, with_default=False)

            if extra_rule and extra_rule.preprocess:
                key = extra_rule.preprocess(key)

            if extra_rule and extra_rule.transform:
                yield extra_rule.transform(key)
            # / TO HERE

            elif isinstance(key, str):
                pass
            # JavaScript is weakly typed for these, so it makes sense to
            # also allow them.  Many encoders seem to do something like this.
            elif isinstance(key, float):
                # see comment for int/float in _make_iterencode
                key = _floatstr(key)
            elif key is True:
                key = "true"
            elif key is False:
                key = "false"
            elif key is None:
                key = "null"
            elif isinstance(key, int):
                # see comment for int/float in _make_iterencode
                key = _intstr(key)
            elif _skipkeys:
                continue
            else:
                raise TypeError(f"keys must be str, int, float, bool or None, " f"not {key.__class__.__name__}")
            if first:
                first = False
            else:
                yield item_separator
            yield _encoder(key)
            yield _key_separator

            # CHANGED FROM HERE:
            extra_rule = rule_cb(value, with_default=False)

            if extra_rule and extra_rule.preprocess:
                value = extra_rule.preprocess(value)

            if extra_rule and extra_rule.transform:
                yield extra_rule.transform(value)
            # / TO HERE

            elif isinstance(value, str):
                yield _encoder(value)
            elif value is None:
                yield "null"
            elif value is True:
                yield "true"
            elif value is False:
                yield "false"
            elif isinstance(value, int):
                # see comment for int/float in _make_iterencode
                yield _intstr(value)
            elif isinstance(value, float):
                # see comment for int/float in _make_iterencode
                yield _floatstr(value)
            else:
                if isinstance(value, (list, tuple)):
                    chunks = _iterencode_list(value, _current_indent_level)
                elif isinstance(value, dict):
                    chunks = _iterencode_dict(value, _current_indent_level)
                else:
                    chunks = _iterencode(value, _current_indent_level)
                yield from chunks
        if newline_indent is not None:
            _current_indent_level -= 1
            yield "\n" + indent_str * _current_indent_level
        yield "}"
        if markers is not None:
            del markers[markerid]

    def _iterencode(o: Any, _current_indent_level: Int) -> IterencodeGenerator:
        # CHANGED FROM HERE:
        extra_rule: JSONRule = rule_cb(o, with_default=False)

        if extra_rule and extra_rule.preprocess:
            o = extra_rule.preprocess(o)

        if extra_rule and extra_rule.transform:
            yield extra_rule.transform(o)
        # / TO HERE

        # default:
        elif isinstance(o, str):
            yield _encoder(o)
        elif o is None:
            yield "null"
        elif o is True:
            yield "true"
        elif o is False:
            yield "false"
        elif isinstance(o, int):
            # see comment for int/float in _make_iterencode
            yield _intstr(o)
        elif isinstance(o, float):
            # see comment for int/float in _make_iterencode
            yield _floatstr(o)
        elif isinstance(o, (list, tuple)):
            yield from _iterencode_list(o, _current_indent_level)
        elif isinstance(o, dict):
            yield from _iterencode_dict(o, _current_indent_level)
        else:
            if markers is not None:
                markerid = id(o)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = o
            o = _default(o)
            yield from _iterencode(o, _current_indent_level)
            if markers is not None:
                del markers[markerid]

    return _iterencode
