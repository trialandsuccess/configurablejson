import json
import typing
from datetime import datetime

from configurablejson import ConfigurableJsonEncoder, JSONRule


class DummyEncoder(ConfigurableJsonEncoder):
    # example that does the same as default
    def rules(self, o, with_default=True):
        return JSONRule()


class SetEncoder(ConfigurableJsonEncoder):
    # example with preprocess

    def rules(self, o, with_default=True):
        if isinstance(o, set):
            return JSONRule(preprocess=list)

        return JSONRule()


class MyClass:
    def tojson(self):
        # already spits out json
        return '["my", "data", "as", "json"]'


class ToJSONEncoder(ConfigurableJsonEncoder):
    # example with transform
    def rules(self, o, with_default=True):
        if hasattr(o, "tojson"):
            return JSONRule(transform=lambda o: o.tojson())

        return JSONRule()


class MyEncoder(ConfigurableJsonEncoder):
    def _default(self, o):
        if hasattr(o, "as_dict"):
            return o.as_dict()
        elif hasattr(o, "asdict"):
            return o.asdict()
        elif hasattr(o, "_asdict"):
            return o._asdict()
        elif hasattr(o, "_as_dict"):
            return o._as_dict()
        elif hasattr(o, "to_dict"):
            return o.to_dict()
        elif hasattr(o, "todict"):
            return o.todict()
        elif hasattr(o, "_todict"):
            return o._todict()
        elif hasattr(o, "_to_dict"):
            return o._to_dict()
        elif hasattr(o, "__json__"):
            return o.__json__()

        return str(o)

    @staticmethod
    def is_probably_namedtuple(o):
        return isinstance(o, tuple) and hasattr(o, "_fields")

    def rules(self, o, with_default=True) -> JSONRule:
        """
        Custom rules for the DD json: set to list and namedtuple to dict
        """

        if self.is_probably_namedtuple(o):
            _type = typing.NamedTuple
        else:
            _type = type(o)

        # other rules:
        return {
            # convert set to list
            set: JSONRule(preprocess=lambda o: list(o)),
            # convert namedtuple to dict
            typing.NamedTuple: JSONRule(preprocess=self._default),
        }.get(_type, JSONRule(preprocess=self._default) if with_default else None)


class Letters(typing.NamedTuple):
    a: str
    b: str
    c: str


class ComplexTupleChild(typing.NamedTuple):
    d: dict[str, dict]
    l: list[dict]
    t: tuple
    s: dict[str, set]
    dt: datetime


class ComplexTupleParent(typing.NamedTuple):
    child: ComplexTupleChild


if __name__ == '__main__':
    data = ComplexTupleParent(ComplexTupleChild(
        {'a': {'b': ['c']}},
        [{'d': 'e'}],
        (1, [], {}, set()),
        {'a': set([1, 2, 3])},
        datetime.today()
    ))

    print(
        json.dumps(data, cls=MyEncoder)
    )
