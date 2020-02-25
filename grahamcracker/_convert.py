import sys
import ast
import inspect
import textwrap
from typing_inspect_isle import class_typevar_mapping
from dataclasses import (
    is_dataclass,
    MISSING as DC_MISSING,
    asdict,
    fields as dc_fields,
    Field as DCField,
)
from typing import (
    Any,
    Type,
    Dict,
    cast,
    Union,
    Mapping,
    Optional,
    TypeVar,
    Tuple,
    Callable,
    List,
)
from typing_inspect_isle import (
    is_optional_type,
    is_union_type,
    get_args,
    is_generic_type,
    get_origin,
    is_typevar,
)
from marshmallow import fields, Schema
from marshmallow.fields import Field
from collections.abc import Mapping as MappingABC

from ._settings_classes import (
    HandlerType,
    _SchemaGenSettings,
    _FieldGenSettings,
    Garams,
    DEFAULT,
)
from ._field_conversion import FIELD_CONVERSION
from ._schema_classes import DataSchemaConcrete
from ._field_classes import NestedOptional
from ._schema_classes import DataSchema
from ._fast_conversion import FastEncoder

DEFAULT_SCHEMA: Type[DataSchemaConcrete] = DataSchema


SchemaType = TypeVar("SchemaType", bound=DataSchemaConcrete)


def dataclass_schema(
    data_class: Any,
    schema_base: Type[SchemaType] = DEFAULT_SCHEMA,  # type: ignore
    type_handlers: "Optional[Dict[Type[Any], Type[HandlerType]]]" = None,
    add_handler: bool = True,
) -> Type[SchemaType]:
    """
    Converts a dataclass to a Marshmallow schema

    :param data_class: dataclass to convert
    :param schema_base: ``marshmallow.Schema`` class to subclass
    :param type_handlers: ``{type, Schema}`` mapping of existing schemas to use for
        given type.
    :param add_handler: Whether to add this schema to ``type_handlers``.

    :return: Subclass of ``schema_base`` with dataclass fields converted to Marshmallow
        fields.
    """

    settings = _configure_settings(data_class, schema_base, type_handlers)
    class_dict = _get_schema_dict(schema_base, settings)

    this_schema = type(f"{data_class.__name__}Schema", (schema_base,), class_dict)
    this_schema = cast(Type[Schema], this_schema)

    # add schema as new type handler.
    if add_handler and type_handlers is not None:
        type_handlers[data_class] = this_schema

    # generate the fast encoder for this schema.
    class SchemaFastEncoder(FastEncoder, type_handlers=type_handlers):  # type: ignore
        pass

    this_schema._FAST_ENCODER = SchemaFastEncoder  # type: ignore

    return this_schema  # type: ignore


def schema_for(
    data_class: Any,
    type_handlers: "Optional[Dict[Type[Any], Type[HandlerType]]]" = None,
    add_handler: bool = True,
) -> Callable[[Type[SchemaType]], Type[SchemaType]]:
    """
    Class decorator for Schema class that adds marshmallow fields for ``data_class``

    :param data_class: class to alter schema for
    :param type_handlers: ``{type, Schema}`` mapping of existing schemas to use for
        given type.
    :return: Same schema class object passed in, with added fields for ``data_class``
    """

    def class_gen(schema_class: Type[SchemaType]) -> Type[SchemaType]:
        gen_class = dataclass_schema(
            data_class, schema_class, type_handlers, add_handler=add_handler
        )

        existing_dict = dict(schema_class.__dict__)
        existing_dict.update(gen_class.__dict__)

        existing_dict.pop("__doc__")

        for name, item in existing_dict.items():
            setattr(schema_class, name, item)

        # If the schema doesn't have it's own doc string, use the one from the
        # dataclass.
        if schema_class.__doc__ is None:
            schema_class.__doc__ = data_class.__doc__

        # add schema as new type handler.
        if add_handler and type_handlers is not None:
            type_handlers[data_class] = schema_class

        return schema_class

    return class_gen


def _configure_settings(
    data_class: Type[Any],
    schema_base: Type[SchemaType],
    type_handlers: "Optional[Dict[Type[Any], Type[HandlerType]]]",
) -> _SchemaGenSettings:
    """sets up schema settings based on params"""
    if not is_dataclass(data_class) or not isinstance(data_class, type):
        raise ValueError(f"{data_class} is not dataclass type")

    if type_handlers is None:
        type_handlers = dict()

    docstrings = get_dataclass_field_docstrings(data_class)

    settings = _SchemaGenSettings(data_class, schema_base, type_handlers, docstrings)

    # remove any handlers who's types are being properly handled.
    default_converters = {
        k: v for k, v in FIELD_CONVERSION.items() if k not in settings.type_handlers
    }
    settings.type_handlers.update(default_converters)

    return settings


def _get_schema_dict(
    schema: Type[Schema], settings: _SchemaGenSettings
) -> Dict[str, Any]:
    """Monkey-patches marshmallow fields to schema"""
    class_dict: Dict[str, Any] = dict()
    if sys.version_info[:2] >= (3, 7):
        class_typevar_mapping(settings.data_class, settings.type_var_index)

    this_field: DCField
    for this_field in dc_fields(settings.data_class):
        class_dict[this_field.name] = _convert_type(this_field, settings)

    if issubclass(schema, DataSchemaConcrete):
        class_dict["__model__"] = settings.data_class

        f: DCField
        class_dict["_dump_only"] = [
            f.name
            for f in dc_fields(settings.data_class)
            if f.metadata is not None and f.metadata.get("garams", Garams()).dump_only
        ]

    return class_dict


def _convert_type(
    data_field: Union[DCField, Type], schema_settings: _SchemaGenSettings
) -> fields.Field:
    """Converts dataclass field to Marshmallow field"""
    settings = _FieldGenSettings(data_field, schema_settings)

    if is_typevar(settings.type) and sys.version_info[:2] >= (3, 7):
        _unpack_type_var(settings)
    settings.type, settings.optional = _unpack_optional(settings.type)
    if is_typevar(settings.type) and sys.version_info[:2] >= (3, 7):
        _unpack_type_var(settings)

    settings.type, optional_second = _unpack_optional(settings.type)
    settings.optional = settings.optional or optional_second

    _validate_type(settings.type)

    settings.data_handler = _get_handler_type(settings)

    if issubclass(settings.data_handler, Schema):
        settings.args = (settings.data_handler,)
        settings.data_handler = fields.Nested
    elif (
        is_dataclass(settings.type)
        and settings.type not in settings.schema_settings.type_handlers
    ):
        # We make a nested schema if a dataclass does not already have a type handler
        nested_schema = dataclass_schema(
            settings.type,
            # We need to pass a clean base here, as the incoming one might have
            # validators and the like attached to it from a decorated schema.
            schema_base=DataSchemaConcrete,
            type_handlers=schema_settings.type_handlers,
        )
        settings.args = (nested_schema,)
    elif is_generic_type(settings.type):
        _get_interior_fields(settings)

    _generate_field_options(settings)

    marshmallow_field = settings.data_handler(*settings.args, **settings.kwargs)

    return marshmallow_field


def _unpack_type_var(settings: _FieldGenSettings) -> None:
    try:
        settings.type = settings.schema_settings.type_var_index[settings.type]
    except KeyError:
        raise TypeError(f"Label '{settings.type}' does not have concrete type")


def _validate_type(field_type: Any) -> None:
    """checks for bad field types"""
    if is_union_type(field_type):
        raise TypeError("model fields cannot contain unions")

    if field_type is Any:
        raise TypeError("model fields cannot have type Any")

    if not is_generic_type(field_type):
        if issubclass(field_type, (list, tuple)):
            raise TypeError("model field collections must be generic type with args")


def _get_handler_type(settings: _FieldGenSettings) -> Type[HandlerType]:
    """Gets Marshmallow field/schema based on type"""
    for handler_type, handler in settings.schema_settings.type_handlers.items():
        test_type = get_origin(settings.type) or settings.type
        if issubclass(test_type, handler_type):
            return handler

    if is_dataclass(settings.type):
        return NestedOptional

    raise TypeError(f"No type handler exists for {settings.type}")


def _add_field_default(settings: _FieldGenSettings) -> None:
    """
    Determines defaults for Marshmallow Field and adds them as kwargs for Marshmallow
    fields
    """
    # if a field, has a default or default factory, we can add that to the object
    settings.data_field = cast(DCField, settings.data_field)
    if settings.data_field.default is not DC_MISSING:
        settings.kwargs["required"] = False
        settings.kwargs["missing"] = settings.data_field.default
        settings.kwargs["default"] = settings.data_field.default
    elif settings.data_field.default_factory is not DC_MISSING:  # type: ignore
        settings.kwargs["required"] = False
        settings.kwargs["missing"] = settings.data_field.default_factory  # type: ignore
        settings.kwargs["default"] = settings.data_field.default_factory  # type: ignore
    else:
        settings.kwargs["required"] = True


def _generate_field_options(settings: _FieldGenSettings) -> None:
    """generates the options for Marshmallow's Field class"""

    if settings.data_field is not None:
        _add_field_default(settings)
    else:
        settings.kwargs["required"] = True

    # if a field is optional, it is not required
    if settings.optional:
        settings.kwargs["allow_none"] = True
    else:
        settings.kwargs["allow_none"] = False

    if settings.data_field is None or settings.data_field.metadata is None:
        return

    # apply docstrings
    try:
        docstring = settings.schema_settings.field_docstrings[settings.data_field.name]
    except KeyError:
        pass
    else:
        settings.kwargs["description"] = docstring

    # handle passed marshmallow params
    try:
        passed_kwargs: Garams = settings.data_field.metadata["garams"]
    except KeyError:
        return

    settings.kwargs.update(
        (key, value)
        for key, value in asdict(passed_kwargs).items()
        if value is not DEFAULT
    )

    # if something is required, marshmallow disallows defaults, so we'll remove those.
    if settings.kwargs["required"]:
        settings.kwargs.pop("missing", None)
        settings.kwargs.pop("default", None)


def _get_interior_fields(settings: _FieldGenSettings) -> None:
    """
    Converts inner fields of a generic to options/arguments for it's Marshmallow
    container.
    """
    inner_fields: List[Field] = [
        _convert_type(t, settings.schema_settings) for t in get_args(settings.type)
    ]

    if get_origin(settings.type) in [Mapping, dict, MappingABC]:
        settings.kwargs["keys"] = inner_fields[0]
        settings.kwargs["values"] = inner_fields[1]
    elif len(inner_fields) == 1 and isinstance(inner_fields[0], fields.Nested):
        # We need to handle lists of schemas differently, so that kwargs are passed
        # to them at runtime.
        inner = inner_fields[0]

        settings.data_handler = NestedOptional
        settings.args = (inner.nested,)
        settings.kwargs["many"] = True
        if inner.allow_none is True:  # type: ignore
            settings.optional = True
    else:
        settings.args = tuple(inner_fields)


def _filter_none_type(data_type: Type) -> bool:
    """Filters out NoneType when getting union args"""
    if is_typevar(data_type):
        return True
    if issubclass(data_type, type(None)):
        return False
    return True


def _unpack_optional(data_type: Type) -> Tuple[Type, bool]:
    """gets type of optional type"""
    # we need to unpack optional types, which are really just unions with None
    optional = False
    while is_optional_type(data_type):
        optional = True
        data_types = tuple(t for t in get_args(data_type) if _filter_none_type(t))

        if len(data_types) > 1:
            raise TypeError("model fields cannot contain unions")
        data_type = data_types[0]

    return data_type, optional


def get_dataclass_field_docstrings(data_class: Type[Any]) -> Dict[str, str]:
    docstring_dict: Dict[str, str] = dict()
    _recurse_dataclass_for_docstrings(data_class, docstring_dict)
    return docstring_dict


def _format_field_docstring(docstring: str) -> str:
    """
    Remove leading and trailing newlines from multi-line descriptions, as it can affect
    formatting of redoc and other documentation tools.
    """
    docstring = textwrap.dedent(docstring)
    description = docstring.strip("\n").rstrip("\n")

    # Add a period for consistency.
    if not description.endswith("."):
        description += "."

    # Capitalize first letter for consistency.
    first_letter = description[0]
    capitalized = first_letter.capitalize()

    description = capitalized + description[1:]

    return description


def _recurse_dataclass_for_docstrings(
    data_class: Type[Any], current_dict: Dict[str, str]
) -> None:
    if is_dataclass(data_class):

        try:
            source = inspect.getsource(data_class)
        except OSError:
            pass
        else:
            source = textwrap.dedent(source)
            parsed = ast.parse(source)
            is_attr = False

            for item in parsed.body[0].body:  # type: ignore
                if hasattr(item, "target"):
                    is_attr = True
                    attr_name = item.target
                    continue

                if is_attr and hasattr(item, "value"):
                    if attr_name.id not in current_dict:
                        description: str = _format_field_docstring(item.value.s)
                        current_dict[attr_name.id] = description
                elif not hasattr(item, "target"):
                    is_attr = False

    for this_class in data_class.__bases__:
        _recurse_dataclass_for_docstrings(this_class, current_dict)
