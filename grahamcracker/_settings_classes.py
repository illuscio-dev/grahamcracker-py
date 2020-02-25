from dataclasses import (
    dataclass,
    InitVar,
    field as dc_field,
    Field as DCField,
    MISSING,
    _MISSING_TYPE,
)
from typing import (
    Any,
    Type,
    Dict,
    Optional,
    Union,
    Iterable,
    TypeVar,
    Callable,
    MutableMapping,
)
from marshmallow import Schema, fields


HandlerType = Union[fields.Field, Schema]


class DEFAULT:
    pass


T = TypeVar("T")
Default = Union[T, Type[DEFAULT], None]


@dataclass
class Garams:
    """Dataclass for passing marshamllow field options in dataclass field metadata"""

    default: Default[Any] = DEFAULT
    missing: Default[Any] = DEFAULT
    attribute: Default[str] = DEFAULT
    data_key: Default[str] = DEFAULT
    validate: Default[Callable] = DEFAULT
    required: Default[bool] = DEFAULT
    allow_none: Default[bool] = DEFAULT
    load_only: Default[bool] = DEFAULT
    dump_only: Default[bool] = DEFAULT
    error_messages: Default[Dict[str, str]] = DEFAULT
    metadata: Default[Dict[str, Any]] = DEFAULT


def gfield(
    *,
    default: Any = MISSING,
    default_factory: Union[_MISSING_TYPE, Callable[[], Any]] = MISSING,
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[MutableMapping[str, Any]] = None,
    garams: Optional[Garams] = None
) -> DCField:
    """As ``dataclasses.field``, but garams can be passed directly"""
    if garams is not None:
        if metadata is None:
            metadata = dict()
        metadata["garams"] = garams

    return dc_field(  # type: ignore
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
        metadata=metadata,
    )


@dataclass
class _SchemaGenSettings:
    data_class: Any
    base: Type[Schema]
    type_handlers: "Dict[Type[Any], Type[HandlerType]]"
    field_docstrings: Dict[str, str]
    type_var_index: "Dict[TypeVar, Type]" = (  # type: ignore
        dc_field(default_factory=dict)
    )


@dataclass
class _FieldGenSettings:
    # passed settings
    _data_field: InitVar[Union[DCField, Type]]
    schema_settings: _SchemaGenSettings

    # calculated settings
    type: Type = dc_field(init=False)
    data_field: Optional[DCField] = dc_field(init=False, default=None)

    # data holders
    args: Iterable[Any] = dc_field(init=False, default_factory=tuple)
    kwargs: Dict[str, Any] = dc_field(init=False, default_factory=dict)
    data_handler: Type[HandlerType] = dc_field(init=False)
    optional: bool = dc_field(init=False)

    def __post_init__(self, _data_field: Union[DCField, Type]) -> None:
        if isinstance(_data_field, DCField):
            self.data_field = _data_field
            self.type = _data_field.type
        else:
            self.type = _data_field
