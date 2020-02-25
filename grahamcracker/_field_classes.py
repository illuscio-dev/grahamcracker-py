from marshmallow import fields, Schema, missing
from typing import (
    TypeVar,
    Any,
    Optional,
    Sequence,
    Union,
    Dict,
    List,
    cast,
    Set,
    Generator,
)


ObjType = TypeVar("ObjType")

DeserializeResult = Union[ObjType, List[ObjType]]
SerializeResult = Union[Dict[str, Any], List[Dict[str, Any]]]

DeserializationValue = Union[SerializeResult, Generator[Dict[str, Any], None, None]]
SerializationValue = Union[SerializeResult, Generator[ObjType, None, None]]


def _filter_nested_item_list(
    value: Optional[Any], index: int, none_indexes: set
) -> bool:
    if value is None:
        none_indexes.add(index)
        return False
    else:
        return True


class NestedOptional(fields.Nested):
    """
    As ``marshmallow.fields.Nested``, but allows for None values if ``allow_none`` is
    set to True.
    """

    # TODO: Find a more performant way to solve this issue. For long lists this could
    #  add a fair amount of overhead.

    def __init__(
        self,
        nested: Schema,
        default: Any = missing,
        exclude: Union[Sequence[str], Set[str]] = tuple(),
        only: Optional[Union[Sequence[str], Set[str]]] = None,
        allow_none: bool = False,
        **kwargs: Any
    ):
        super().__init__(
            nested=nested,
            default=default,
            exclude=exclude,
            only=only,  # type: ignore
            **kwargs
        )
        self.allow_none: bool = allow_none

    def _deserialize(  # type: ignore
        self,
        value: SerializeResult,
        attr: str,
        data: Union[dict, List],
        partial: Optional[Union[bool, List[str]]] = None,
        **kwargs: Any
    ) -> DeserializeResult:
        none_indexes: Set[int] = set()

        if self.allow_none is True and isinstance(value, list):
            value_pass: DeserializationValue = (
                v
                for i, v in enumerate(value)
                if _filter_nested_item_list(v, i, none_indexes)
            )
        else:
            value_pass = value

        deserialized = super()._deserialize(value_pass, attr, data, partial, **kwargs)

        for index in none_indexes:
            deserialized = cast(list, deserialized)
            deserialized.insert(index, None)

        return deserialized

    def _serialize(  # type: ignore
        self, nested_obj: DeserializeResult, attr: str, obj: Any, **kwargs: Any
    ) -> SerializeResult:
        none_indexes: Set[int] = set()

        if self.allow_none is True and isinstance(nested_obj, list):
            pass_nested: SerializationValue = (
                v
                for i, v in enumerate(nested_obj)
                if _filter_nested_item_list(v, i, none_indexes)
            )
        else:
            pass_nested = nested_obj

        serialized = super()._serialize(pass_nested, attr, obj, **kwargs)

        for index in none_indexes:
            serialized = cast(list, serialized)
            serialized.insert(index, None)

        return serialized
