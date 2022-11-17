# Configurable JSON Encoder

By default, the json.Encoder class' logic can only be customized to a certain extent:

- a 'default' method can be overwritten to encode objects that JSON can't serialize by default;
- an 'encode' method can be overwritten to fully rewrite the encoding logic, which is powerful but can be hard to change
  if you need to change the specific behavior for a type in a nested structure;
- an 'iterencode' method can be overwritten to handle the recursive behavior of the JSON encoder, but this method uses
  functions under the hood that are not defined as class methods but rather as functions in the encoder
  module (`c_make_encoder` and `_make_iterencode`), which thus can not be overwritten by class inheritance.

This module aims to help make adding custom rules to the JSON encoder easier, by injecting a middle
layer `ConfigurableJsonEncoder` which essentially uses a copied and slightly modified version of `_make_iterencode` from
the original module.

Some examples of things you can do with this module (see examples.py for the actual rules)

```python
from examples import *

data = {
    'original': ['behavior'],
    'set': {1, 2, 3},
    'namedtuple': Letters('a', 'b', 'c'),
    "class": MyClass()
}
try:
    print(json.dumps(data))
except TypeError:
    ...  # Object of type set is not JSON serializable

# default behavior without type error:
print(json.dumps(data, default=str))
# {"original": ["behavior"], "set": "{1, 2, 3}", "namedtuple": ["a", "b", "c"], "class": "<__main__.MyClass object at 0x...>"}

# the same behavior as above
print(json.dumps(data, cls=DummyEncoder))
# {"original": ["behavior"], "set": "{1, 2, 3}", "namedtuple": ["a", "b", "c"], "class": "<__main__.MyClass object at 0x...>"}

# encodes set into a list:
print(json.dumps(data, cls=SetEncoder))
# {"original": ["behavior"], "set": [1, 2, 3], "namedtuple": ["a", "b", "c"], "class": "<__main__.MyClass object at 0x...>"}

# calls .tojson() which uses transform to output a string
print(json.dumps(data, cls=ToJSONEncoder))
# {"original": ["behavior"], "set": "{1, 2, 3}", "namedtuple": ["a", "b", "c"], "class": ["my", "data", "as", "json"]}

# converts namedtuple to a dictionary instead of a list (the default behavior)
print(json.dumps(data, cls=MyEncoder))
# {"original": ["behavior"], "set": [1, 2, 3], "namedtuple": {"a": "a", "b": "b", "c": "c"}, "class": {"my data": ["as", "a", "dict"]}}

```

## Usage:

Simply extend `ConfigurableJsonEncoder` with a `rules` method that returns a `JSONRule` or `None` based on the
input `o` (which is one unit in the nested data tree). Again, see `examples.py` for inspiration.