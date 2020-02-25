.. automodule:: grahamcracker

Basic Usage
-----------

A traditional model/schema interaction would need to look like this:

>>> from dataclasses import dataclass
>>> from marshmallow import Schema, post_load, pre_dump, fields
>>>
>>> @dataclass
... class BookModel:
...     title: str
...     author: str
...     copies_sold: int
...     copyright_year: int
>>>
>>> class BookSchema(Schema):
...     title = fields.Str()
...     author = fields.Str()
...     copies_sold = fields.Int()
...     copyright_year = fields.Int()
...
...     @post_load
...     def load_obj(self, data: dict):
...         return Book(**data)
...
...     @pre_dump
...     def dump_obj(self, data: BookModel):
...         return asdict(data)
...
>>>
>>> book_data = {
...     "title": "Harry Potter",
...     "author": "JK Rowling",
...     "copies_sold": 1000000000,
...     "copyright_year": "1994"
... }
>>>
>>> book = BookSchema().load(book_data)
>>> book
BookModel(title='Harry Potter', author='JK Rowling', copies_sold=1000000000, ...
>>> book.author
'JK Rowling'


**Why this sucks:** In this model, we need to duplicate our work, defining the model in
``dataclasses`` semantics, then re-defining *again* in ``marshmallow`` semantics. This:

   * Creates busywork
   * Is more error-prone (were field names typed *exactly* the same each time?)
   * Is harder to maintain (must update your model in two places)
   * Suuuuuucks

Before python 3.7, there wasn't a great way around it. You could have something that
auto-generated model classes based on marshmallow schemas, but doing so robs one of the
main benefits of deserializing to a data-holding class over using a dict: IDE
auto-completion from defined, introspectable classes.

The code itself could be generated, then copied / pasted, but wpu;d have to be done
every time the code updated, and tweaks to the generated code run the risk of being
lost.

Looking at the above example, it should be obvious that as of 3.6+, type-hinted
dataclasses have all of the information we need to enforce our schema. Lets add some
graham cracker around this marshmallow:

>>> from grahamcracker import dataclass_schema
>>>
>>> @dataclass
... class BookModel:
...     title: str
...     author: str
...     copies_sold: int
...     copyright_year: int
...
>>> BookSchema = dataclass_schema(BookModel)
>>> book = BookSchema().load(book_data)
>>> book
BookModel(title='Harry Potter', author='JK Rowling', copies_sold=1000000000, ...)

That's it! ``grahamcracker`` generated a marshmallow schema for you! Validate and load
your data with ease:

>>> book_data = {
...     "title": "Harry Potter",
...     "author": "JK Rowling",
...     "copies_sold": 1000000000,
...     "copyright_year": "Not a number"
... }
>>> book = BookSchema().load(book_data)
Traceback (most recent call last):
   ...
marshmallow.exceptions.ValidationError: {'copyright_year': ['Not a valid integer.']}

A decorator version is also available:

>>> from grahamcracker import schema_for
>>>
>>> @schema_for(BookModel)
... class BookSchema(DataSchema[BookModel]):
...     pass
...
>>> book = BookSchema().load(book_data)
>>> book
BookModel(title='Harry Potter', author='JK Rowling', copies_sold=1000000000, ...)
