import marshmallow
from dataclasses import is_dataclass, asdict
from json import JSONEncoder
from typing import Any, Type, Optional, Tuple, Dict

from ._field_conversion import FIELD_CONVERSION, HandlerType
from ._load_dataclass import MISSING


NoneType = type(None)
JSON_TYPES: Tuple[Type, ...] = (
    str,
    dict,
    int,
    float,
    bool,
    list,
    tuple,
    NoneType,  # type: ignore
)


def generate_converter_dict(
    type_handlers: "Dict[Type[Any], Type[HandlerType]]",
) -> "Dict[Type[Any], HandlerType]":
    """
    Takes the type handlers used to generate data schemas and weeds out the ones
    needed to generate a fast encoder, then initialized them.
    """
    result: "Dict[Type[Any], HandlerType]" = dict()

    for t, c in type_handlers.items():
        if not isinstance(t, type):
            continue
        if t not in JSON_TYPES:
            add = True
            for json_type in JSON_TYPES:
                if issubclass(t, json_type):
                    add = False
            if add:
                result[t] = c()

    return result


DEFAULT_CONVERTERS: "Dict[Type[Any], HandlerType]" = generate_converter_dict(
    FIELD_CONVERSION
)


class FastEncoder(JSONEncoder):
    """Meant to be subclassed for any given Dataschema"""

    CONVERTERS: "Dict[Type[Any], HandlerType]" = DEFAULT_CONVERTERS

    def __init_subclass__(
        cls,
        type_handlers: Optional["Dict[Type[Any], Type[HandlerType]]"] = None,
        **kwargs: Any
    ):
        if type_handlers is None:
            cls.CONVERTERS = DEFAULT_CONVERTERS
        else:
            cls.CONVERTERS = generate_converter_dict(type_handlers)

    def default(self, obj: Any) -> Any:
        if is_dataclass(obj):
            data = {k: v for k, v in asdict(obj).items() if v is not MISSING}
            return data
        else:
            converter = self.CONVERTERS[type(obj)]

            # Schemas are only registered for dataclasses, so we are safe to assume
            # the converter will always be a field. since dict objects will get the
            # dict field.
            assert not isinstance(converter, marshmallow.Schema)

            value = converter._serialize(obj, "attr", {})
            return value
