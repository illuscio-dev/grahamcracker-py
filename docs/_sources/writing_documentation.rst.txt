.. automodule:: grahamcracker

Writing Documentation
=====================

Docstrings
----------

Grahamcracker has a few built-in features for helping with documentation of you schemas.

If a schema is not given it's own docstring, it will inherit the docstring of the
dataclass:

>>> @dataclass
... class Name:
...     """Names are auditory designations that humans give one another."""
...     first: str
...     last: str
...
>>> @schema_for(Name)
... class NameSchema(DataSchema[Name]):
...     pass
...
>>> Name.__doc__
'Names are auditory designations that humans give one another.'
>>> NameSchema.__doc__
'Names are auditory designations that humans give one another.'

Field Descriptions
------------------

Docstrings appearing after a field will be captured as ``'description'`` metadata for
compatibility with swagger generation libraries like `apistar`_

>>> @dataclass
... class Annotated:
...     key: str
...     """a description for key"""

Note that the collection of these descriptions is handled through
``inspect.get_source``, which matches the first class with the correct name. In cases
where two different classes in different scopes of the same file share the same name,
the wrong descriptions may be pulled.

.. _apistar: http://polyglot.ninja/api-star-python-3-api-framework/
