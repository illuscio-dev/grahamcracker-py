.. automodule:: grahamcracker

API Specification
=================

dataclass_schema()
------------------

.. autofunction:: dataclass_schema

@schema_for
-----------

.. autofunction:: schema_for

DataSchema Base Class
---------------------

.. autoclass:: DataSchemaConcrete
   :members:

   Generically-typed subclass of ``marshmallow.Schema``.

   Allows for Generic typing with model for help with autom-completion and mypy

   >>> schema: DataSchema[Book] = dataclass_schema(Book)

   or:

   >>> @schema_for(Book)
   ... class BookSchema(DataSchema[Book])
   ...     pass

   :class:`DataSchema` implements sane default for serializing / deserializing
   dataclasses using marshmallow's ``post_load`` and ``pre-dump`` methods. See below.

   ``.load()``, ``.loads()``, ``.dump()``, ``.dumps()`` and ``.validate()`` are
   re-implemented with no alterations to add type-hinting for a more robust mypy
   experience.

Garams dataclass
----------------

.. class:: Garams

   All attributed correspond to a param of marshmallow.fields.Field. All fields
   have a default value of ``DEFAULT``, and will not overwrite the auto-calculated
   values from grahamcracker.

   Passing ``None`` to a value will force the param to ``None`` when it is passed to
   the field.

   The field names and their possible values are listed here, for more information on
   how they affect a field, see the `marshmallow`_ documentation.

   Fields:
      **default**: ``Union[Any, None, DEFAULT]``

      **missing**: ``Union[Any, None, DEFAULT]``

      **attribute**: ``Union[str, None, DEFAULT]``

      **data_key**: ``Union[str, None, DEFAULT]``

      **validate**: ``Union[Callable, None, DEFAULT]``

      **required**: ``Union[bool, None, DEFAULT]``

      **allow_none**: ``Union[bool, None, DEFAULT]``

      **load_only**: ``Union[bool, None, DEFAULT]``

      **dump_only**: ``Union[bool, None, DEFAULT]``

      **error_messages**: ``Union[Dict[str, str], None, DEFAULT]``

      **metadata**: ``Union[Dict[str, Any], None, DEFAULT]``

NestedOptional Field
--------------------

.. autoclass:: NestedOptional
   :members:

.. _marshmallow: https://marshmallow.readthedocs.io/en/3.0/