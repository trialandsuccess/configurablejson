# json_extra

import dataclasses
import json.encoder as e
from abc import ABC, abstractmethod

import typing


@dataclasses.dataclass
class JSONRule:
    preprocess: typing.Callable[[typing.Any], typing.Any] = None
    transform: typing.Callable[[typing.Any], str] = None


def _make_iterencode(
        rule_cb,
        markers,
        _default,
        _encoder,
        _indent,
        _floatstr,
        _key_separator,
        _item_separator,
        _sort_keys,
        _skipkeys,
        _one_shot,
        ## HACK: hand-optimized bytecode; turn globals into locals
        ValueError=ValueError,
        dict=dict,
        float=float,
        id=id,
        int=int,
        isinstance=isinstance,
        list=list,
        str=str,
        tuple=tuple,
        _intstr=int.__repr__,
):
    # stolen from json.encoder and changed

    if _indent is not None and not isinstance(_indent, str):
        _indent = " " * _indent

    def _iterencode_list(lst, _current_indent_level):
        if not lst:
            yield "[]"
            return
        if markers is not None:
            markerid = id(lst)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        buf = "["
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = "\n" + _indent * _current_indent_level
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
            yield "\n" + _indent * _current_indent_level
        yield "]"
        if markers is not None:
            del markers[markerid]

    def _iterencode_dict(dct, _current_indent_level):
        if not dct:
            yield "{}"
            return
        if markers is not None:
            markerid = id(dct)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = dct
        yield "{"
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = "\n" + _indent * _current_indent_level
            item_separator = _item_separator + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = _item_separator
        first = True
        if _sort_keys:
            items = sorted(dct.items())
        else:
            items = dct.items()
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
                raise TypeError(
                    f"keys must be str, int, float, bool or None, "
                    f"not {key.__class__.__name__}"
                )
            if first:
                first = False
            else:
                yield item_separator
            yield _encoder(key)
            yield _key_separator

            # CHANGED FROM HERE:
            extra_rule: JSONRule = rule_cb(value, with_default=False)

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
            yield "\n" + _indent * _current_indent_level
        yield "}"
        if markers is not None:
            del markers[markerid]

    def _iterencode(o, _current_indent_level):
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


class ConfigurableJsonEncoder(e.JSONEncoder, ABC):
    """
    You can extend this JSON Encoder with your own rules(obj) method that returns a JSONRule,
    which has a preprocess and/or a transform method.
    """

    @abstractmethod
    def rules(self, o) -> JSONRule:
        """
        Should return a JSONRule with either a preprocess and/or a transorm method.
        The preprocess will run before the transform and any regular encoding logic.
         This can be useful to e.g. convert a set() to a list() before encoding it and its contents,

        the transform will run after the preprocess and instead of regular json encoding logic.
        This can be useful to fully overwrite the logic on some object (type)


        """

        raise NotImplementedError("Please implement rules after extending this class.")

    def default(self, o) -> str:
        rule: JSONRule = self.rules(o)

        if rule and rule.preprocess:
            o = rule.preprocess(o)

        if rule and rule.transform:
            return rule.transform(o)

        return str(o)

    def iterencode(self, o, _one_shot=False):
        # copied from json.encoder

        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = e.encode_basestring_ascii
        else:
            _encoder = e.encode_basestring

        def floatstr(
                o,
                allow_nan=self.allow_nan,
                _repr=float.__repr__,
                _inf=e.INFINITY,
                _neginf=-e.INFINITY,
        ):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:
                text = "NaN"
            elif o == _inf:
                text = "Infinity"
            elif o == _neginf:
                text = "-Infinity"
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " + repr(o)
                )

            return text

        # never use c_iterencode
        _iterencode = _make_iterencode(
            self.rules,
            markers,
            self.default,
            _encoder,
            self.indent,
            floatstr,
            self.key_separator,
            self.item_separator,
            self.sort_keys,
            self.skipkeys,
            _one_shot,
        )

        return _iterencode(o, 0)
