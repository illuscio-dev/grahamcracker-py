.. islelib documentation master file, created by
   sphinx-quickstart on Mon Oct  1 00:18:03 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. automodule:: grahamcracker

grahamcracker-py
===================================

grahamcracker goes great with marshmallow! Use ``grahamcracker`` to automatically make
`marshmallow`_ schemas from dataclasses.

>>> import uuid
>>> from grahamcracker import DataSchema, schema_for
>>> from dataclasses import dataclass
>>>
>>> @dataclass
... class Name:
...     id: uuid.UUID
...     first: str
...     last: str
...
>>> @schema_for(Name)
... class NameSchema(DataSchema[Name]):
...     pass
...
>>> name_id = "fbd6283c-1963-4493-bf1e-b69ae28ee8f6"
>>> name_data = {"first": "Harry", "last": "Potter", "id": name_id}
>>>
>>> name = NameSchema().load(name_data)
>>> name
Name(id=UUID('fbd6283c-1963-4493-bf1e-b69ae28ee8f6'), first='Harry', last='Potter')
>>>
>>> dumped = NameSchema().dump(name)
>>> dumped
{'first': 'Harry', 'last': 'Potter', 'id': 'fbd6283c-1963-4493-bf1e-b69ae28ee8f6'}

The uuid is automatically serialized / deserialized and the dataclass is handled
seamlessly.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   self
   ./basic_usage
   ./pre_recs
   ./quickstart
   ./writing_documentation
   ./api_guide

.. _marshmallow: https://marshmallow.readthedocs.io/en/3.0/
.. _dacite: https://github.com/konradhalas/dacite
.. _dataclasses: https://docs.python.org/3/library/dataclasses.html
.. _typing: https://docs.python.org/3/library/typing.html
.. _great primer: https://mypy.readthedocs.io/en/latest/cheat_sheet_py3.html
.. _mypy: https://mypy.readthedocs.io/en/latest/
.. _much deeper dive: https://realpython.com/python-type-checking/
.. _apistar: http://polyglot.ninja/api-star-python-3-api-framework/
