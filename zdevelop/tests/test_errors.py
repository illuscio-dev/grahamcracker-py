import pytest
from dataclasses import dataclass
from fractions import Fraction
from typing import Union, Any, List, Dict
from marshmallow import ValidationError

from grahamcracker import dataclass_schema, DataSchemaConcrete
from zdevelop.tests.conftest import min_version
from zdevelop.tests.test_schema import (
    HasTypeVar,
    OptionalConcrete,
    HasEmail,
    HasURL,
    HasDateTime,
    HasTime,
    HasDate,
)


class TestSchemaGenErrors:
    def test_simple_schema(self):
        @dataclass
        class X:
            pass

        schema = dataclass_schema(X)
        assert issubclass(schema, DataSchemaConcrete)
        assert isinstance(schema, type)
        assert schema.__name__ == "XSchema"

    def test_non_dataclass_raises(self):
        class Thing:
            pass

        with pytest.raises(ValueError):
            dataclass_schema(Thing)

    def test_dataclass_non_optional_raises(self):
        @dataclass
        class X:
            text: str

        schema = dataclass_schema(X)

        with pytest.raises(ValidationError):
            obj = schema().load({"text": None})

    def test_dataclass_no_default_load_raises(self):
        @dataclass
        class X:
            text: str

        schema = dataclass_schema(X)
        with pytest.raises(ValidationError):
            loaded = schema().load(dict())
            print(f"loaded: {loaded}")

    def test_dataclass_nested_load_non_optional_raises(self):
        @dataclass
        class X:
            text: str

        @dataclass
        class Y:
            x: X
            number: int

        schema = dataclass_schema(Y)

        data = {"x": {"text": None}, "number": 10}

        with pytest.raises(ValidationError):
            loaded = schema().load(data)
            print(loaded)

    def test_true_union_raises(self):
        @dataclass
        class X:
            key: Union[str, int]

        with pytest.raises(TypeError):
            dataclass_schema(X)

    def test_any_raises(self):
        @dataclass
        class X:
            key: Any

        with pytest.raises(TypeError):
            dataclass_schema(X)

    def test_any_list_raises(self):
        @dataclass
        class X:
            key: List[Any]

        with pytest.raises(TypeError):
            dataclass_schema(X)

    def test_any_dict_raises(self):
        @dataclass
        class X:
            key: Dict[Any, Any]

        with pytest.raises(TypeError):
            dataclass_schema(X)

    def test_base_list_raises(self):
        @dataclass
        class X:
            key: list

        with pytest.raises(TypeError):
            dataclass_schema(X)

    def test_base_unknown_type_raises(self):
        @dataclass
        class X:
            key: Fraction

        with pytest.raises(TypeError):
            dataclass_schema(X)

    def test_union_optional_type_raises(self):
        @dataclass
        class X:
            key: Union[None, str, bool]

        with pytest.raises(TypeError):
            dataclass_schema(X)

    @min_version
    def test_unresolved_typevar_raises(self):
        with pytest.raises(TypeError):
            dataclass_schema(HasTypeVar)

    @min_version
    def test_typevar_wrong_type_raises(self):
        schema = dataclass_schema(OptionalConcrete)
        result = schema().validate({"value": int})
        assert "value" in result

    def test_invalid_email_raises(self):
        schema = dataclass_schema(HasEmail)
        result = schema().validate({"value": "not an e-mail"})
        assert "value" in result

    def test_invalid_url_raises(self):
        schema = dataclass_schema(HasURL)
        result = schema().validate({"value": "not a URL"})
        assert "value" in result

    def test_invalid_datetime_raises(self):
        schema = dataclass_schema(HasDateTime)
        result = schema().validate({"value": "not a datetime"})
        assert "value" in result

    def test_invalid_datetime_raises(self):
        schema = dataclass_schema(HasTime)
        result = schema().validate({"value": "not a datetime"})
        assert "value" in result

    def test_invalid_datetime_raises(self):
        schema = dataclass_schema(HasDate)
        result = schema().validate({"value": "not a date"})
        assert "value" in result
