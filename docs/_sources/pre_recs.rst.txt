.. automodule:: grahamcracker

Before You Get Started
======================

Background Reading
------------------

It is recommended that you be familiar with the following python libraries:

   * `dataclasses`_
   * `typing`_
   * `marshmallow`_

`typing`_ can be a lot to take in if you are relatively unfamiliar with Python's new
type-hinting system or `mypy`_. Here is a `great primer`_ on typing
in python 3, as well as a `much deeper dive`_.

Compatibility
-------------

* **Python 3.6+**: ``dataclasses`` is required.

* **Select features require Python 3.7+**: Due to the evolution of the ``typing``
  module. They will be called out in this documentation.

* **marshmallow 3.0.0+**: (Currently in pre-release) due to API changes this library
  depends on.

.. _marshmallow: https://marshmallow.readthedocs.io/en/3.0/
.. _dacite: https://github.com/konradhalas/dacite
.. _dataclasses: https://docs.python.org/3/library/dataclasses.html
.. _typing: https://docs.python.org/3/library/typing.html
.. _great primer: https://mypy.readthedocs.io/en/latest/cheat_sheet_py3.html
.. _mypy: https://mypy.readthedocs.io/en/latest/
.. _much deeper dive: https://realpython.com/python-type-checking/