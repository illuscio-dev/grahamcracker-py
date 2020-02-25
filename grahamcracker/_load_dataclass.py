# The early version of this lib depended on dacite to load dataclasses. This section
# allows a very light-wieght way to load a dataclass from a dict.

# This functionality does not handle loading nested dataclasses or the like -- all of
# that is handled through marshamllow. Neither does any validation occur -- again, that
# is handled by marshmallow.

from dataclasses import fields, Field, FrozenInstanceError, MISSING as DC_MISSING
from typing import Dict, Any, TypeVar, Type, Tuple


class _MissingType:
    """Singleton class. All instances of MISSING are the same object."""

    _instance = None

    def __repr__(self) -> str:
        return "<VALUE MISSING>"

    def __new__(cls) -> "_MissingType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


MISSING = _MissingType()

DataClassType = TypeVar("DataClassType")


def dataclass_from_dict(
    data_class: Type[DataClassType], data: Dict[str, Any], use_defaults: bool
) -> DataClassType:
    """Loads validated / deserialized dict into dataclass model."""
    kwargs, post_init_values = _build_attribute_dicts(data_class, data, use_defaults)

    # Pass all values as **kwargs into the dataclass.
    data_instance = data_class(**kwargs)  # type: ignore

    # Fields where init=False need to be set after-the-fact.
    for name, value in post_init_values.items():
        try:
            setattr(data_instance, name, value)
        except FrozenInstanceError:
            # A type error means this dataclass is a frozen. We can get around that for
            # post-init fields by setting the attribute through object.
            object.__setattr__(data_instance, name, value)  # type: ignore

    return data_instance


def _build_attribute_dicts(
    data_class: Type[DataClassType], data: Dict[str, Any], use_defaults: bool
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Build dict for init **kwargs and post-init values.

    :param data_class: dataclass to load instance of
    :param data: dict to load into dataclass
    :param use_defaults: Whether to use field default. If False, MISSING is used.

    :return: init values, post-init values
    """
    kwargs: Dict[str, Any] = dict()
    post_init_values: Dict[str, Any] = dict()

    data_field: Field
    for data_field in fields(data_class):
        # Remove processed values, use missing as default if it is not present.
        try:
            value = data.pop(data_field.name)
        except KeyError:
            # If a value was not supplied, we are going to let the dataclass generate
            # it's default value or MISSING if there is no default value. If we are
            # using defaults the defaults should already be there from the load.
            if not use_defaults:
                value = MISSING
            elif data_field.default is not DC_MISSING:
                value = data_field.default
            elif data_field.default_factory is not DC_MISSING:  # type: ignore
                value = data_field.default_factory()  # type: ignore
            else:
                value = MISSING

        if data_field.init:
            kwargs[data_field.name] = value
        else:
            post_init_values[data_field.name] = value

    return kwargs, post_init_values
