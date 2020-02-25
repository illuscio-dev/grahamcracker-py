import pytest
import json
import datetime
import pytz
import uuid
from dataclasses import dataclass, field, asdict
from typing import (
    Optional,
    List,
    Dict,
    Any,
    Generic,
    TypeVar,
    Mapping,
)
from marshmallow import ValidationError, Schema, fields, post_load, pre_dump, validates
from fractions import Fraction


from grahamcracker import (
    dataclass_schema,
    DataSchemaConcrete,
    DataSchema,
    Garams,
    schema_for,
    EmailStr,
    URLStr,
    gfield,
    MISSING,
)
from zdevelop.tests.conftest import min_version


@dataclass
class Simple:
    text: str


@dataclass
class SimpleOptional:
    text: Optional[str]


@dataclass
class SimpleDefault:
    text: str = "value"


@dataclass
class HasBool:
    value: bool


@dataclass
class HasList:
    text_list: List[str]


@dataclass
class HasListDefault:
    text_list: List[str] = field(default_factory=list)


@dataclass
class HasDict:
    int_mapping: Dict[str, int]


@dataclass
class HasBaseDict:
    int_mapping: dict


@dataclass
class HasNoArgsDict:
    int_mapping: Dict


@dataclass
class SimpleNested:
    text: str


@dataclass
class SimpleRoot:
    nested: SimpleNested


@dataclass
class OptionalNested:
    text: Optional[str]


@dataclass
class OptionalRoot:
    nested: OptionalNested


@dataclass
class ListNested:
    text: str


@dataclass
class ListRoot:
    nested: List[ListNested]


def must_be_10(value: int) -> bool:
    return value == 10


@dataclass
class HasValidator:
    num: int = field(metadata={"garams": Garams(validate=must_be_10)})


Var = TypeVar("Var")


@dataclass
class HasTypeVar(Generic[Var]):
    value: Var


@dataclass
class ConcreteTypeVar(HasTypeVar[str]):
    pass


@dataclass
class OptionalGeneric(Generic[Var]):
    value: Optional[Var]


@dataclass
class OptionalConcrete(OptionalGeneric[str]):
    pass


@dataclass
class HasEmail:
    value: EmailStr


@dataclass
class HasURL:
    value: URLStr


test_uuid = uuid.uuid4()
test_datetime = datetime.datetime.now(tz=pytz.UTC)
test_date = datetime.date.today()
test_time = datetime.time(hour=12)


@dataclass
class HasUUID:
    value: uuid.UUID


@dataclass
class HasDateTime:
    value: datetime.datetime


@dataclass
class HasDate:
    value: datetime.date


@dataclass
class HasTime:
    value: datetime.time


class FractionSchema(Schema):
    numerator = fields.Int()
    denominator = fields.Int()

    @post_load
    def load_obj(self, data: dict, *, many: bool, partial: bool):
        print(data)
        return Fraction(numerator=data["numerator"], denominator=data["denominator"])

    @pre_dump
    def dump_obj(self, data: Fraction, *, many: bool):
        return {"numerator": data.numerator, "denominator": data.denominator}


class FractionField(fields.Field):
    def _deserialize(self, value: str, attr: str, obj: dict, **kwargs: Any) -> Fraction:
        return Fraction(value)

    def _serialize(self, value: Fraction, attr: str, data: dict, **kwargs: Any) -> str:
        return str(value)


@dataclass
class HasFractions:
    frac: Fraction


@dataclass
class HasOptionalListItems:
    simple_list: List[Optional[Simple]]


@dataclass
class HasOptionalDataclass:
    simple: Optional[Simple]


@dataclass(frozen=True)
class FrozenPostInit:
    key: str = field(init=False)

    @classmethod
    def generate(cls):
        result = cls()
        object.__setattr__(result, "key", "value")
        return result


class TestLoadDump:
    param_list = [
        (Simple("value"), {"text": "value"}, None, None),
        (SimpleOptional("value"), {"text": "value"}, None, None),
        (SimpleOptional(None), {"text": None}, None, None),
        (SimpleDefault(), dict(), None, {"text": "value"}),
        (
            HasList(["value1", "value2"]),
            {"text_list": ["value1", "value2"]},
            None,
            None,
        ),
        (HasListDefault(), {}, None, {"text_list": []}),
        (
            HasDict({"one": 1, "two": 2}),
            {"int_mapping": {"one": 1, "two": 2}},
            None,
            None,
        ),
        (
            HasBaseDict({"one": 1, "two": 2}),
            {"int_mapping": {"one": 1, "two": 2}},
            None,
            None,
        ),
        (SimpleRoot(SimpleNested("value")), {"nested": {"text": "value"}}, None, None),
        (
            OptionalRoot(OptionalNested("value")),
            {"nested": {"text": "value"}},
            None,
            None,
        ),
        (OptionalRoot(OptionalNested(None)), {"nested": {"text": None}}, None, None),
        (
            ListRoot([ListNested("value1"), ListNested("value2")]),
            {"nested": [{"text": "value1"}, {"text": "value2"}]},
            None,
            None,
        ),
        pytest.param(
            ConcreteTypeVar("answer"),
            {"value": "answer"},
            None,
            None,
            marks=min_version,
        ),
        pytest.param(
            OptionalConcrete("answer"),
            {"value": "answer"},
            None,
            None,
            marks=min_version,
        ),
        pytest.param(
            OptionalConcrete(None), {"value": None}, None, None, marks=min_version
        ),
        (
            HasEmail(EmailStr("someone@gmail.com")),
            {"value": "someone@gmail.com"},
            None,
            None,
        ),
        (
            HasURL(URLStr("https://www.google.com")),
            {"value": "https://www.google.com"},
            None,
            None,
        ),
        (HasUUID(test_uuid), {"value": str(test_uuid)}, None, None),
        (HasDateTime(test_datetime), {"value": test_datetime.isoformat()}, None, None),
        (HasDate(test_date), {"value": test_date.isoformat()}, None, None),
        (HasTime(test_time), {"value": test_time.isoformat()}, None, None),
        (HasBool(True), {"value": True}, None, None),
        (HasBool(False), {"value": False}, None, None),
        # Optional List Data First
        (
            HasOptionalListItems([Simple("value"), None]),
            {"simple_list": [{"text": "value"}, None]},
            None,
            None,
        ),
        # Optional List Data Middle
        (
            HasOptionalListItems([None, Simple("value"), None]),
            {"simple_list": [None, {"text": "value"}, None]},
            None,
            None,
        ),
        # Optional List Data Last
        (
            HasOptionalListItems([None, Simple("value")]),
            {"simple_list": [None, {"text": "value"}]},
            None,
            None,
        ),
        # Optional List Data Spread
        (
            HasOptionalListItems(
                [None, Simple("value"), Simple("value"), None, Simple("value")]
            ),
            {
                "simple_list": [
                    None,
                    {"text": "value"},
                    {"text": "value"},
                    None,
                    {"text": "value"},
                ]
            },
            None,
            None,
        ),
        (HasOptionalDataclass(None), {"simple": None}, None, None),
        (FrozenPostInit.generate(), {"key": "value"}, None, None),
    ]

    @pytest.mark.parametrize(
        "data_obj, data_dict, data_answer, dict_answer", param_list
    )
    @pytest.mark.parametrize("operation", ["load", "dump", "validate"])
    @pytest.mark.parametrize("use_decorator", [False, True])
    @pytest.mark.parametrize("fast_dump", [False, True])
    @pytest.mark.parametrize("load_dataclass", [False, True])
    def test_load_dump(
        self,
        use_decorator: bool,
        operation: str,
        data_obj: Any,
        data_dict: dict,
        data_answer: Optional[Any],
        dict_answer: Optional[dict],
        fast_dump: bool,
        load_dataclass: bool,
    ):
        if use_decorator:

            @schema_for(type(data_obj))
            class TestSchema(DataSchemaConcrete):
                pass

            schema = TestSchema
        else:
            schema = dataclass_schema(type(data_obj))

        if operation == "load":
            print("DATA DICT:", data_dict)
            print("DATA OBJ:", data_obj)
            loaded = schema(load_dataclass=load_dataclass).load(data_dict)

            if data_answer is not None:
                data_obj = data_answer

            if load_dataclass is False:
                data_obj = asdict(data_obj)

            assert loaded == data_obj
            assert isinstance(loaded, type(data_obj))

        elif operation == "dump":
            if not fast_dump:
                dumped = schema().dump(data_obj)
            else:
                dumped_str = schema(fast_dumps=True).dumps(data_obj)
                dumped = json.loads(dumped_str)

            if dict_answer is not None:
                data_dict = dict_answer

            assert dumped == data_dict
            assert isinstance(dumped, dict)

        elif operation == "validate":
            assert schema().validate(data_dict) == dict()

    def test_dump_from_non_dict(self):
        class CustomMapping(Mapping):
            def __init__(self, data: dict):
                self.data = data

            def __getitem__(self, k):
                return self.data[k]

            def __len__(self) -> int:
                return len(self.data)

            def __iter__(self):
                return iter(self.data)

        schema_class = dataclass_schema(Simple)
        data = CustomMapping({"text": "value"})

        schema = schema_class()

        dumped = schema.dumps(data)
        loaded = schema.loads(dumped)

        assert loaded.text == "value"


class TestPartial:
    def test_partial(self):
        @dataclass
        class PartialData:
            field1: str
            field2: str

        schema = dataclass_schema(PartialData)
        loaded: PartialData = schema().load({"field2": "two"}, partial=("field1",))

        assert loaded.field1 is MISSING
        assert loaded.field2 == "two"

    def test_partial_raises(self):
        @dataclass
        class PartialData:
            field1: str
            field2: str

        schema = dataclass_schema(PartialData)
        with pytest.raises(ValidationError):
            loaded: PartialData = schema().load({"field2": "two"})

    def test_load_partial_generic(self):
        @dataclass
        class X:
            value1: int
            value2: int

        schema = dataclass_schema(X)
        assert schema(partial=True).load({"value1": 1}) == X(1, MISSING)

    def test_load_partial_default(self):
        @dataclass
        class X:
            value1: int
            value2: int = 2

        schema = dataclass_schema(X)
        assert schema(partial=True).load({"value1": 1}) == X(1, MISSING)

    def test_load_partial_default_factory(self):
        @dataclass
        class X:
            value1: int
            value2: int = field(default_factory=int)

        schema = dataclass_schema(X)
        assert schema(partial=True).load({"value1": 1}) == X(1, MISSING)

    def test_exclude_nested(self):
        @dataclass
        class X:
            key1: str
            key2: str

        @dataclass
        class Y:
            x_list: List[X]

        schema = dataclass_schema(Y)
        loaded = schema(exclude=["x_list.key1"]).load({"x_list": [{"key2": "value"}]})

        assert loaded.x_list[0].key2 == "value"
        assert loaded.x_list[0].key1 is MISSING

    def test_exclude_nested_root(self):
        @dataclass
        class X:
            key1: str
            key2: str

        @dataclass
        class Y:
            key: str
            x_list: List[X]

        schema_type = dataclass_schema(Y)
        schema = schema_type(only=["key"])
        loaded = schema.load({"key": "value"})

        assert loaded.x_list is MISSING
        assert loaded.key == "value"

        assert schema.dump(loaded) == {"key": "value"}

    def test_load_partial_missing(self):
        @dataclass
        class X:
            key1: str
            key2: uuid.UUID

        schema_type = dataclass_schema(X)
        schema = schema_type(partial=True)
        dumped = schema.dump(X(key1="value", key2=MISSING))

        assert dumped == {"key1": "value"}

    def test_datetime_missing(self):
        @dataclass
        class X:
            key1: str
            key2: datetime.datetime

        @dataclass
        class Y:
            key_root: str
            x_list: List[X]

        @schema_for(Y)
        class YSchema(DataSchema[Y]):
            pass

        schema = YSchema(exclude=["key_root", "x_list.key2"])
        dumped = schema.dump(
            Y(key_root=MISSING, x_list=[X(key1="value", key2=MISSING)])
        )

        assert dumped == {"x_list": [{"key1": "value"}]}


class TestOtherSchemas:
    def test_load_with_type_schema(self):

        data_dict = {"frac": {"numerator": 3, "denominator": 4}}
        data = HasFractions(Fraction("3/4"))

        schema = dataclass_schema(
            HasFractions, type_handlers={Fraction: FractionSchema}
        )

        loaded = schema().load(data_dict)
        print(f"loaded: {loaded}")

        assert loaded == data

    def test_dump_with_type_schema(self):

        data_dict = {"frac": {"numerator": 3, "denominator": 4}}
        data = HasFractions(Fraction("3/4"))

        schema = dataclass_schema(
            HasFractions, type_handlers={Fraction: FractionSchema}
        )

        dumped = schema().dump(data)
        print(f"dumped: {dumped}")

        assert dumped == data_dict

    def test_load_with_type_field(self):

        data_dict = {"frac": "3/4"}
        data = HasFractions(Fraction("3/4"))

        schema = dataclass_schema(HasFractions, type_handlers={Fraction: FractionField})

        loaded = schema().load(data_dict)
        print(f"loaded: {loaded}")

        assert loaded == data

    def test_dump_with_type_field(self):

        data_dict = {"frac": "3/4"}
        data = HasFractions(Fraction("3/4"))

        schema = dataclass_schema(HasFractions, type_handlers={Fraction: FractionField})

        dumped = schema().dump(data)
        print(f"dumped: {dumped}")

        assert dumped == data_dict

    def test_dataclass_field_handler(self):
        @dataclass
        class DataType:
            value: Any

        class DataTypeField(fields.Field):
            def _serialize(self, value: DataType, attr, obj, **kwargs) -> Any:
                return {"value": value["value"]}

            def _deserialize(self, value, attr, data, **kwargs) -> DataType:
                return DataType(value["value"])

        @dataclass
        class X:
            data: DataType

        schema = dataclass_schema(X, type_handlers={DataType: DataTypeField})

        assert schema().load({"data": {"value": 10}}) == X(DataType(10))
        assert schema().dump(X(DataType(10))) == {"data": {"value": 10}}

    def test_exclude_field(self):
        @dataclass
        class X:
            field1: str
            field2: str

        schema_type = dataclass_schema(X)
        schema = schema_type(exclude=["field1"])

        data = {"field2": "value2"}
        loaded: X = schema.load(data)
        print(f"loaded: {loaded}")

        assert loaded.field1 is MISSING
        assert loaded.field2 == "value2"

        dumped = schema.dump(loaded)
        print(f"dumped: {dumped}")

        assert dumped == data

        loaded.field1 = "value1"
        dumped = schema.dump(loaded)
        print(f"dumped: {dumped}")

        assert dumped == data

    def test_normalize_many_load(self):
        @dataclass
        class X:
            key: str

        schema_type = dataclass_schema(X)
        default_schema = schema_type(many=True)
        normalize_schema = schema_type(many=True, normalize_many=True)

        data = {"key": "value"}

        with pytest.raises(ValidationError):
            default_schema.load(data)

        loaded = normalize_schema.load(data)
        assert loaded == [X("value")]


class TestGarams:
    def test_validator_passes(self):
        schema = dataclass_schema(HasValidator)
        data = {"num": 10}

        assert len(schema().validate(data)) == 0

    def test_validator_fails(self):
        schema = dataclass_schema(HasValidator)
        data = {"num": 11}

        data_dict = schema().dump(data)
        result = schema().validate(data_dict)

        assert len(result) == 1
        assert "num" in result

    def test_field_required(self):
        @dataclass
        class X:
            text: str = field(
                default="value", metadata={"garams": Garams(required=True)}
            )

        schema = dataclass_schema(X)

        result = schema().validate({})
        assert len(result) == 1
        assert "text" in result

    def test_field_required_garams(self):
        @dataclass
        class X:
            text: str = gfield(default="value", garams=Garams(required=True))

        schema = dataclass_schema(X)

        result = schema().validate({})
        assert len(result) == 1
        assert "text" in result

    def test_schema_does_not_inherit_validators(self):
        @dataclass
        class X:
            value: str

        @dataclass
        class Y:
            number: int
            x: X

        type_handlers = dict()

        @schema_for(Y, type_handlers=type_handlers)
        class YSchema(DataSchemaConcrete):
            @validates("number")
            def check_number_less_than_four(self, value: int):
                assert value < 4

        x_schema = type_handlers[X]

        assert not hasattr(x_schema, "check_number_less_than_four")

        serialized = YSchema().dump(Y(3, X("test")))
        assert YSchema().validate(serialized) == dict()

    def test_schema_write_protection(self):
        @dataclass
        class X:
            value1: str
            value2: str

        @schema_for(X)
        class XSchema(DataSchemaConcrete):
            WRITE_PROTECTED = ["value2"]

        protected_schema = XSchema.write_protected()
        data = {"value1": "value"}

        assert protected_schema.validate(data) == dict()

        data["value2"] = "value"
        assert "value2" in protected_schema.validate(data)

    @min_version
    def test_schema_write_protection_data_schema_typed(self):
        from grahamcracker import DataSchema

        @dataclass
        class X:
            value1: str
            value2: str

        @schema_for(X)
        class XSchema(DataSchema[X]):
            WRITE_PROTECTED = ["value2"]

        protected_schema = XSchema.write_protected()
        data = {"value1": "value"}

        assert protected_schema.validate(data) == dict()

        data["value2"] = "value"
        assert "value2" in protected_schema.validate(data)


class TestLoadDefaults:
    def test_regular_default(self):
        @dataclass
        class X:
            value1: int
            value2: int = 2

        schema = dataclass_schema(X)
        loaded: X = schema(partial=True, use_defaults=True).load({"value1": 1})

        assert loaded.value1 == 1
        assert loaded.value2 == 2

    def test_factory_default(self):
        @dataclass
        class X:
            value1: int
            value2: int = field(default_factory=int)

        schema = dataclass_schema(X)
        loaded: X = schema(partial=True, use_defaults=True).load({"value1": 1})

        assert loaded.value1 == 1
        assert loaded.value2 == 0

    def test_no_default_still_missing(self):
        @dataclass
        class X:
            value1: int
            value2: int

        schema = dataclass_schema(X)
        loaded: X = schema(partial=True, use_defaults=True).load({"value1": 1})

        assert loaded.value1 == 1
        assert loaded.value2 is MISSING


class TestTypeHandlers:
    def test_type_handler_add_func(self):
        @dataclass
        class X:
            key: str

        type_handlers = {}

        XSchema = dataclass_schema(X, type_handlers=type_handlers)

        assert type_handlers[X] is XSchema

    def test_type_handler_add_func_false(self):
        @dataclass
        class X:
            key: str

        type_handlers = {}

        _ = dataclass_schema(X, type_handlers=type_handlers, add_handler=False)

        assert X not in type_handlers

    def test_type_handler_add_decorator(self):
        @dataclass
        class X:
            key: str

        type_handlers = {}

        @schema_for(X, type_handlers=type_handlers)
        class XSchema(DataSchemaConcrete):
            pass

        assert type_handlers[X] is XSchema

    def test_type_handler_add_decorator_false(self):
        @dataclass
        class X:
            key: str

        type_handlers = {}

        @schema_for(X, type_handlers=type_handlers, add_handler=False)
        class XSchema(DataSchemaConcrete):
            pass

        assert X not in type_handlers

    def test_nested_handler(self):
        @dataclass
        class X:
            key: str

        @dataclass
        class Y:
            x: X

        type_handlers = {}

        _ = dataclass_schema(Y, type_handlers=type_handlers)

        assert X in type_handlers
        assert Y in type_handlers

    def test_nested_handler_decorator(self):
        @dataclass
        class X:
            key: str

        @dataclass
        class Y:
            x: X

        type_handlers = {}

        @schema_for(Y, type_handlers=type_handlers)
        class XSchema(DataSchemaConcrete):
            pass

        assert X in type_handlers
        assert Y in type_handlers

    def test_nested_handler_custom(self):
        @dataclass
        class X:
            key: str

        @dataclass
        class Y:
            x: X

        type_handlers = {}

        XSchema = dataclass_schema(X, type_handlers=type_handlers)
        assert type_handlers[X] is XSchema

        YSchema = dataclass_schema(Y, type_handlers=type_handlers)

        assert type_handlers[X] is XSchema
        assert type_handlers[Y] is YSchema

    def test_nested_handler_custom_decorator(self):
        @dataclass
        class X:
            key: str

        @dataclass
        class Y:
            x: X

        type_handlers = {}

        @schema_for(X, type_handlers=type_handlers)
        class XSchema(DataSchemaConcrete):
            pass

        assert type_handlers[X] is XSchema

        @schema_for(Y, type_handlers=type_handlers)
        class YSchema(DataSchemaConcrete):
            pass

        assert type_handlers[X] is XSchema
        assert type_handlers[Y] is YSchema

    def test_custom_type_converter(self):
        class UUIDCustom(fields.UUID):
            set_value = None

            def _serialize(self, *args, **kwargs):
                UUIDCustom.set_value = "something"
                return super()._serialize(*args, **kwargs)

        @dataclass
        class WithUUID:
            id: uuid.UUID

        type_handlers = {uuid.UUID: UUIDCustom}

        schema = dataclass_schema(WithUUID, type_handlers=type_handlers)

        assert type_handlers[uuid.UUID] is UUIDCustom

        assert UUIDCustom.set_value is None
        schema().dump(WithUUID(uuid.uuid4()))
        assert UUIDCustom.set_value == "something"


def test_marshmallow_method_validators():
    @schema_for(Simple)
    class SimpleSchema(DataSchemaConcrete):
        @validates("text")
        def validate_text(self, value: str) -> None:
            if value != "value":
                raise ValidationError("'text' must be 'value'")

    schema = SimpleSchema()

    result = schema.validate({"text": "thing"})
    print(result)
    assert len(result) == 1

    result = schema.validate({"text": "value"})
    print(result)
    assert len(result) == 0
