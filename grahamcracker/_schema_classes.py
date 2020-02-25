import dataclasses
import json
from typing import (
    TypeVar,
    Generic,
    Type,
    Union,
    Optional,
    Any,
    Tuple,
    List,
    Dict,
    Mapping,
    Sequence,
    Set,
)
from marshmallow import Schema, pre_load, post_load, pre_dump

from ._load_dataclass import dataclass_from_dict
from ._load_dataclass import _MissingType, MISSING
from ._fast_conversion import FastEncoder


ObjType = TypeVar("ObjType")
RecordType = Mapping[str, Any]
LoadType = Union[RecordType, List[RecordType]]
DumpType = Union[RecordType, List[RecordType], ObjType, List[ObjType]]


# NOTE:
# There are a NUMBER of type: ignore comments throughout this code. Marshmallow's typing
# while good for auto-complete, is not implemented correctly for its subclassing API
# in many cases. It also uses implicit Optional arguments, while grahamcracker uses
# explicit optional arguments. Therefore a number of static type check errors need to
# be ignored.


class DataSchemaConcrete(Schema):
    __model__: Type[ObjType]  # type: ignore

    WRITE_PROTECTED: List[str] = list()
    """
    This attribute is reserved for fields that should be protected in write-methods
    like a POST or PATCH. To be passed to init as ``exclude`` param when checking
    incoming objects for these methods. It has no actual effect on the schema by itself.
    """

    UPDATE_ALLOWED: List[str] = list()
    """
    Some classes may have a very limited number of attributes that are allowed to be
    updated in a PATCH. This attribute can be used as a consistent way to notate them.
    To be passed to init as ``only`` param when checking incoming objects in these
    methods. It has no actual effect on the schema by itself.
    """

    _FAST_ENCODER: Type[FastEncoder] = FastEncoder

    def __init__(
        self,
        only: Optional[Union[Sequence[str], Set[str]]] = None,
        exclude: Union[Tuple[str, ...], List[str]] = tuple(),
        many: bool = False,
        normalize_many: bool = False,
        context: Optional[dict] = None,
        load_only: Union[Tuple[str, ...], List[str]] = tuple(),
        dump_only: Union[Tuple[str, ...], List[str]] = tuple(),
        partial: Union[Tuple[str, ...], bool] = False,
        unknown: Optional[str] = None,  # type: ignore
        load_dataclass: bool = True,
        use_defaults: bool = False,
        fast_dumps: bool = False,
    ):
        if context is None:
            context = dict()

        # We have to use the context object here so options are passed to nested
        # schemas. Part of this is only setting these options if they are not the
        # default, so that context is not overridden in nested schemas during this init.
        if load_dataclass is False:
            context["load_dataclass"] = load_dataclass

        if use_defaults is True:
            context["use_defaults"] = use_defaults

        self.fast_dumps: bool = fast_dumps
        self.normalize_many: bool = normalize_many

        super().__init__(
            only=only,  # type: ignore
            exclude=exclude,
            many=many,
            context=context,
            load_only=load_only,
            dump_only=dump_only,
            partial=partial,
            unknown=unknown,  # type: ignore
        )

    @property
    def load_dataclass(self) -> bool:
        return self.context.get("load_dataclass", True)

    @property
    def use_defaults(self) -> bool:
        return self.context.get("use_defaults", False)

    def load(  # type: ignore
        self,
        data: LoadType,
        many: Optional[bool] = None,
        partial: Optional[Union[bool, Sequence[str], Set[str]]] = None,
        unknown: Optional[str] = None,
    ) -> Union[ObjType, List[ObjType], dict, List[dict]]:
        """Typed alias of ``marshmallow.Schema.load``"""
        return super().load(
            data,  # type: ignore
            many=many,  # type: ignore
            partial=partial,  # type: ignore
            unknown=unknown,  # type: ignore
        )

    def loads(  # type: ignore
        self,
        data: Union[str, bytes],
        many: Optional[bool] = None,
        partial: Optional[Union[bool, Sequence[str], Set[str]]] = None,
        unknown: Optional[str] = None,
        **kwargs: Any
    ) -> Union[ObjType, List[ObjType], dict, List[dict]]:
        """Typed alias of ``marshmallow.Schema.loads``"""
        return super().loads(
            data,  # type: ignore
            many=many,  # type: ignore
            partial=partial,  # type: ignore
            unknown=unknown,  # type: ignore
            **kwargs
        )

    def dump(
        self, obj: DumpType, many: Optional[bool] = None
    ) -> Union[dict, List[dict]]:
        """Typed alias of ``marshmallow.Schema.dump``"""
        return super().dump(obj, many=many)  # type: ignore

    def dumps(
        self, obj: DumpType, many: Optional[bool] = None, *args: Any, **kwargs: Any
    ) -> str:
        """Typed alias of ``marshmallow.Schema.dumps``"""
        if self.fast_dumps:
            return json.dumps(obj, cls=self._FAST_ENCODER)
        else:
            return super().dumps(obj, many=many, *args, **kwargs)  # type: ignore

    def validate(  # type: ignore
        self,
        data: LoadType,
        many: Optional[bool] = None,
        partial: Optional[Union[bool, Sequence[str], Set[str]]] = None,
    ) -> Union[dict, List[dict]]:
        """Typed alias of ``marshmallow.Schema.validate``"""
        return super().validate(data, many=many, partial=partial)  # type: ignore

    @pre_load(pass_many=True)
    def normalize_many_load(
        self, data: Union[dict, List[dict]], *, many: bool, partial: bool
    ) -> Union[dict, List[dict]]:
        if many and self.normalize_many and not isinstance(data, list):
            return [data]
        else:
            return data

    @post_load(pass_many=False)
    def load_obj(
        self, data: Dict[str, Any], *, many: bool, partial: bool
    ) -> Union[ObjType, dict]:
        """
        ``marshmallow.post-load`` method. Converts to ``self.__model__`` type using
        ``dacite.from_dict()`` and the __model__ dataclass. If partial loading,
        ``dataclasses.MISSING`` is used as any allowed missing values.
        """
        if self.load_dataclass is True:
            return dataclass_from_dict(
                self.__model__, data, use_defaults=self.use_defaults
            )
        else:
            return data

    @pre_dump(pass_many=False)
    def dump_obj(
        self, data: Union[Mapping[str, Any], ObjType, _MissingType], *, many: bool
    ) -> Union[Dict[str, Any], ObjType, _MissingType]:
        """
        ``marshmallow.pre_dump`` method. Passes through dicts, but converts dataclasses
        using ``dataclasses.asdict()``
        """
        dumped: Union[Mapping[str, Any], ObjType, _MissingType]

        if dataclasses.is_dataclass(data):
            dumped = dataclasses.asdict(data)
        else:
            dumped = data

        if isinstance(dumped, Mapping):
            result: Union[Dict[str, Any], ObjType, _MissingType] = {
                k: v for k, v in dumped.items() if v is not MISSING
            }
        else:
            result = dumped

        return result

    @classmethod
    def write_protected(cls, **kwargs: Any) -> "DataSchemaConcrete":
        """
        Returns instantiated schema with ``cls.WRITE_PROTECTED`` passed to ``exclude``
        param (see marshmallow documentation). Intended to allow uniform declaration of
        fields excluded from POST, PATCH, and PUT operations, and more consistent, less
        bug-prone mirroring of that behavior between client and server implementations.
        """
        this_exclude = kwargs.get("exclude", list())
        this_exclude.extend(cls.WRITE_PROTECTED)
        kwargs["exclude"] = this_exclude
        return cls(**kwargs)


class DataSchema(DataSchemaConcrete, Generic[ObjType]):
    @classmethod
    def write_protected(cls, **kwargs: Any) -> "DataSchema[ObjType]":
        """This is just here for the additional type hinting."""
        return super().write_protected(**kwargs)  # type: ignore
