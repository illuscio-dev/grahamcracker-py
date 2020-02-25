.. automodule:: grahamcracker

Quick Start
===========


Grahamcracker Suppositions
--------------------------

``grahamcracker`` makes a couple deductions about each field's settings when translating
from a ``dataclass`` to a marshmallow ``Schema``.

   * Optional Types: pass ``True`` to the ``allow_none`` marshmallow Field param,
     otherwise ``False`` is passed.

   * If the dataclass field has neither a ``default`` or ``default_factory`` value,
     the ``required`` marshmallow Field param is set to ``True``.

   * ``default`` and ``default_factory`` ``dataclass.field()`` values are passed to
     both the ``default`` and ``missing`` marshmallow Field params, and ``required`` is
     set to ``False``.

   * ``Union`` types raise a ``TypeError`` as Marshmallow does not support unions
     natively.

   * ``All``, following the logic above, is also rejected with a ``TypeError``.

   * Marshmallow translates types as follows:

      ======================  ====================
      dataclass type          marshmallow type
      ======================  ====================
      ``EmailStr``\*          ``fields.Email``
      ``URLStr``\*            ``fields.URL``
      ``str``                 ``fields.Str``
      ``int``                 ``fields.Int``
      ``float``               ``fields.Float``
      ``bool``                ``fields.Bool``
      ``list``                ``fields.List``
      ``dict``                ``fields.Dict``
      ``datetime.datetime``   ``fields.DateTime``
      ``datetime.date``       ``fields.Date``
      ``datetime.time``       ``fields.Time``
      ``datetime.timedelta``  ``fields.TimeDelta``
      ``uuid.UUID``           ``fields.UUID``
      ``Mapping``             ``fields.Dict``
      ``Collection``          ``fields.List``
      ======================  ====================

      \* EmailStr and URLStr are subclasses of str supplied by this lib. They are used
      to signal that a field is specifically an e-mail or url so the appropriate
      marshmallow field is used

   * For ``Dict`` or ``List``/``Collection`` types, values passed to the generic type
     will be converted to item or key / value type arguments to their marshmallow
     counterpart.

   * ``dict`` can be passed (no arguments) but ``list`` with no arguments cannot, since
     marshmallow requires that lists have a type, while typing of dict keys and values
     is optional.

   * ``grahamcracker`` will find the first type that passes an ``issubclass()`` check,
     searched in the order above.

   * A ``{type, fields.Field / Schema}`` mapping can be passed to ``type-handlers`` to
     extend the list. User-passed types are checked first.

   * dataclass fields which are themselves dataclasses will have a schema generated for
     them, placed in a ``fields.Nested`` marshmallow field. dataclasses with a schema
     passed to ``type_handlers`` will use that instead of being auto-generated.

   * non-dataclass Types which do not appear in the list above will raise a
     ``TypeError`` unless a field or schema for them is explicitly passed to
     ``type_handlers``.

   * These suppositions can be overridden. See `Pass Marshmallow Field Settings`_,
     and `Supply Existing Schemas`_.


Partial Loading
---------------

Loading a schema with the ``partial`` argument set to ``True`` or a list of field names
to ``exclude``, ``only``, or ``partial`` will result in any missing fields will be set
to ``grahamcracker.MISSING``, EVEN IF THE FIELD HAS A DEFAULT VALUE. This way we
explicitly know what data was passed to the schema to load.

>>> from grahamcracker import MISSING
>>>
>>> @dataclass
... class Name:
...     first: str
...     last: str = "Peake"
...
>>> schema = dataclass_schema(Name)
>>> name = schema(partial=True).load({"first": "Billy"})
>>> name
Name(first='Billy', last=<VALUE MISSING>)
>>> assert name.last is MISSING
True

We can override this behavior by setting ``use_defaults`` to ``True`` when we init the
schema.

>>> schema = dataclass_schema(Name)
>>> name = schema(partial=True, use_defaults=True).load({"first": "Billy"})
>>> name
Name(first='Billy', last='Peake')
>>> assert name.last == "Peake"
True


Loading as Dict
---------------

In some instances it may  be desirable to not load the full dataclass, but return a
dict as marshmallow normally would. To do this, simply set the ``load_dataclass=``
param to ``False``.

>>> name = schema(load_dataclass=False).load({"first": "Billy", "last": "Peake"})
>>> name
{"first": "Billy", "last": "Peake"}


Supply Existing Schemas
-----------------------

Lets say we have the following dataclass, which contains a ``fraction.Fraction``

>>> from fractions import Fraction
>>> from collections import OrderedDict
>>>
>>> @dataclass
... class Ingredient:
...     name: str
...     amount_cups: Fraction
...

And a schema for handling fractions:

>>> class FractionSchema(Schema):
...     numerator = fields.Int()
...     denominator = fields.Int()
...
...     @post_load
...     def load_obj(self, data: dict) -> Fraction:
...         return Fraction(data["numerator"], data["denominator"])
...
...     @pre_dump
...     def dump_obj(self, data: Fraction) -> dict:
...         data_dict = {
...             "numerator": data.numerator,
...             "denominator": data.denominator,
...         }
...         return data_dict

We can supply this schema to :func:`dataclass_schema` like so:

>>> IngredientSchema = dataclass_schema(
...     Ingredient, type_handlers=OrderedDict({Fraction: FractionSchema})
... )
>>>
>>> ingredient_data = {
...     "name": "flour",
...     "amount_cups": {
...         "numerator": 1,
...         "denominator": 4,
...     }
... }
>>> IngredientSchema().load(ingredient_data)
Ingredient(name='flour', amount_cups=Fraction(1, 4))

User-passed type handlers are checked before the default fields listed in
``suppositions``, so custom schemas can be passed for types like ``List`` or ``Dict``

An ``OrderedDict`` is required so the correct type priority can be assured.


Supply Marshmallow Fields
-------------------------

In the above example, instead of having a schema for the fraction type, we could
instead represent it as a string and use a custom field:

>>> from typing import Any
>>>
>>> class FractionField(fields.Field):
...     def _deserialize(
...         self, value: str, attr: str, obj: dict, **kwargs: Any
...     ) -> Fraction:
...         return Fraction(value)
...
...     def _serialize(
...         self, value: Fraction, attr: str, data: dict, **kwargs: Any
...     ) -> str:
...         return str(value)
...
>>> ingredient_data = {
...     "name": "flour",
...     "amount_cups": "3/4"
... }
>>>
>>>
>>> @schema_for(Ingredient, type_handlers=OrderedDict({Fraction: FractionField}))
>>> class IngredientSchema(DataSchema[Ingredient]):
>>>     pass
>>>
>>> IngredientSchema().load(ingredient_data)
Ingredient(name='flour', amount_cups=Fraction(3, 4))
>>>
>>> ingredient_obj = Ingredient("flour", amount_cups="1/4")
>>> IngredientSchema().dump(ingredient_obj)
{'name': 'flour', 'amount_cups': '1/4'}


Pass Marshmallow Field Settings
-------------------------------

The :class:`Garams` dataclass is provided as an easy way to pass params to the
marshmallow field generated for that data. Lets pass a validation function.

>>> from dataclasses import field
>>> from marshmallow import ValidationError
>>> from grahamcracker import Garams
>>>
>>> def validate_name(value: str):
...     # we want to make sure each author has at least a first and last name
...     if len(value.split(" ")) < 2:
...         raise ValidationError("name must contain at least first and last")
...
>>> @dataclass
... class BookModel:
...     title: str
...     author: str = field(metadata={"garams": Garams(validate=validate_name)})
...     copies_sold: int
...     copyright_year: int
...
>>> @schema_for(BookModel)
... class BookSchema(DataSchema[BookModel]):
...     pass
...
>>> book_data = {
...     "title": "Harry Potter",
...     "author": "JK Rowling",
...     "copies_sold": 1000000000,
...     "copyright_year": 1992
... }
>>> BookSchema().validate(book_data)
{}
>>> book_data["author"] = "Jim"
>>> BookSchema().validate(book_data)
{'author': ['name must contain at least first and last']}

Field settings always override grahamcracker's inferred settings.
:func:`grahamcracker.gfield` allows you to pass Garams directly to the ``garams`` param.
The value is passed to the field's metadata as the manual example above.

:func:`grahamcracker.gfield` is otherwise identical to ``dataclasses.field``.

>>> from grahamcracker import gfield
>>>
>>> @dataclass
... class HasDefault:
...     num: int = gfield(default=10, garams=Garams(required=True))
...
>>> @schema_for(HasDefault)
... class HasDefaultSchema(DataSchema[HasDefault]):
...     pass
...
>>> HasDefaultSchema().validate({})
{'num': ['Missing data for required field.']}

Here, `required` would normally be inferred as false since `num` has a default
value, but we have overridden it to tell our API it is, in-fact, required


Use Marshmallow method decorators
---------------------------------

Decorated classes can make use of marshmallow's method decorators, such as the
``marshmallow.validates`` decorator.

>>> from marshmallow import validates, ValidationError
>>>
>>> @dataclass
... class NeedsValidation:
...     num: int
...
>>> @schema_for(NeedsValidation)
... class NeedsValidationSchema(DataSchema[NeedsValidation]):
...     @validates("num")
...     def num_must_be_10(self, value: int):
...         if value != 10:
...             raise ValidationError("value must be 10")
...
{'required': True, 'allow_none': False}
>>> NeedsValidationSchema().validate({"num": 10})
{}
>>> NeedsValidationSchema().validate({"num": 11})
{'num': ['value must be 10']}


Email and URL fields
--------------------

The ``EmailStr`` and ``URLStr`` classes are supplied to signal that values should be
emails or urls. The two classes are unmodified subclasses of ``str``

>>> from dataclasses import dataclass
>>> from grahamcracker import EmailStr, URLStr, dataclass_schema
>>>
>>> @dataclass
... class SpecialStrVals:
...     email: EmailStr
...     url: URLStr
...
>>> schema = dataclass_schema(SpecialStrVals)
>>> good_data = {"email": "someone@gmail.com", "url": "https://google.com"}
>>> bad_data = {"email": "dont't send me spam", "url": "go away"}
>>>
>>> schema().validate(good_data)
{}
>>> schema().validate(bad_data)
{'email': ['Not a valid email address.'], 'url': ['Not a valid URL.']}


Fast Dumps
----------

Often, serialization does not require the overhead for validation and key transformation
that marshmallow provides. Grahamcracker offers a more efficient method for serializing
a json string using the ``fast_dumps=`` param.

This parameter uses a generated json encoder to dump the object. All validation steps
are skipped, as are any Method or Function fields. The one exception is field of
non-json types, which still use the field's `_serialize()` method. Partial options
like, ``partial=``, ``only=`` and ``exclude=`` are ignored. Objects are dumped as-is,
keeping all keys that are not set to ``MISSING``.

>>> from dataclasses import dataclass
>>> from grahamcracker import dataclass_schema
>>> import timeit
>>>
>>> @dataclass
... class Name:
...     first: str
...     last: str
...
>>> NameSchema = dataclass_schema(Name)
>>>
>>> schema_fast = NameSchema(fast_dumps=True)
>>> schema_normal = NameSchema()
>>>
>>> name_data = Name("Harry", "Potter")
>>>
>>> schema_fast.dumps(name_data)
'{"first": "Harry", "last": "Potter"}'
>>>
>>> def normal_dump():
...     schema_normal.dumps(name_data)
...
>>> def fast_dump():
...     schema_fast.dumps(name_data)
...
>>> timeit.timeit(normal_dump, number=10000)
0.23919811100000743
>>> timeit.timeit(fast_dump, number=10000)
0.11337517399999797

On average ``fast_dumps=True`` makes :func:`DataSchemaConcrete.dumps` 2x faster than
using the regular marshmallow method.

**THIS SETTING ONLY WORKS FOR DUMPS**, it has no affect on the behavior of
:func:`DataSchemaConcrete.dump`.


Normalize Many
--------------

The ``normalize_many=`` init param allows schemas with ``many=`` set to ``True`` to load
single documents instead of only lists. The resulting object will always be a list.

>>> name_data_single = {"first": "Harry", "last": "Potter"}
>>> name_data_many = [
...     {"first": "Harry", "last": "Potter"},
...     {"first": "Hermione", "last": "Granger"},
... ]
>>>
>>> normalize_schema = NameSchema(many=True, normalize_many=True)
>>>
>>> normalize_schema.load(name_data_single)
[Name(first='Harry', last='Potter')]
>>> normalize_schema.load(name_data_many)
[Name(first='Harry', last='Potter'), Name(first='Hermione', last='Granger')]

Now the same schema to be used when it is uncertain whether a single document or list of
documents need to be converted.

This option only has an effect on ``load`` / ``loads``, it does not have any effect on
``dump`` / ``dumps``

.. _apistar: http://polyglot.ninja/api-star-python-3-api-framework/
