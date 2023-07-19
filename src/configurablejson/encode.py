"""
Modifies the default json encoder logic.
"""

# json_extra

import dataclasses
import json.encoder as e
import typing
from abc import ABC, abstractmethod

from ._internals import (
    ReprMethod,
    _make_iterencode,
    encode_basestring,
    encode_basestring_ascii,
)


@dataclasses.dataclass
class JSONRule:
    """
    Return type of ConfigurableJsonEncoder.rules.

    Preprocess is called before transform and can return anything,
    Transform is called after preprocess and must return a string.

    Otherwise, str() is called on the result of preprocess.
    If neither preprocess or transform is supplied, only str() is called on the input.
    """

    preprocess: typing.Callable[[typing.Any], typing.Any] | None = None
    transform: typing.Callable[[typing.Any], typing.Any] | None = None


class ConfigurableJsonEncoder(e.JSONEncoder, ABC):
    """
    You can extend this JSON Encoder with your own rules(obj) method that returns a JSONRule, \
    which has a preprocess and/or a transform method.
    """

    @abstractmethod
    def rules(self, o: typing.Any) -> JSONRule:
        """
        Should return a JSONRule with either a preprocess and/or a transorm method.

        The preprocess will run before the transform and any regular encoding logic.
        This can be useful to e.g. convert a set() to a list() before encoding it and its contents,

        The transform will run after the preprocess and instead of regular json encoding logic.
        This can be useful to fully overwrite the logic on some object (type).
        """
        raise NotImplementedError("Please implement rules after extending this class.")

    def default(self, o: typing.Any) -> typing.Any:
        """
        Define the converter method for unsupported types (e.g. list and dict are supported by JSON, but Set is not).
        """
        rule: JSONRule = self.rules(o)

        if rule and rule.preprocess:
            o = rule.preprocess(o)

        if rule and rule.transform:
            return rule.transform(o)

        return str(o)

    def iterencode(self, o: typing.Any, _one_shot: bool = False) -> typing.Iterator[str]:
        """
        Copied from json.encoder.
        """
        markers: typing.Optional[dict[int, typing.Any]] = {} if self.check_circular else None

        _encoder = encode_basestring_ascii if self.ensure_ascii else encode_basestring

        def floatstr(
            o: typing.Any,
            allow_nan: bool = self.allow_nan,
            _repr: ReprMethod = float.__repr__,
            _inf: float = e.INFINITY,
            _neginf: float = -e.INFINITY,
        ) -> str:
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
                raise ValueError("Out of range float values are not JSON compliant: " + repr(o))

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
