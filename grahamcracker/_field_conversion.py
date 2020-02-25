import datetime
import uuid
from collections import OrderedDict
from marshmallow import fields
from typing import Type, Any, Mapping, List, Optional

from ._settings_classes import HandlerType


# These types exist so we can signal that str fields are e-mails or URLs
class EmailStr(str):
    pass


class URLStr(str):
    pass


# Custom fields to properly cast strings back to the types above
class _GCEmail(fields.Email):
    def _deserialize(  # type: ignore
        self,
        value: str,
        attr: Optional[str] = None,
        data: Optional[dict] = None,
        **kwargs: Any
    ) -> EmailStr:
        value = super()._deserialize(value=value, attr=attr, data=data, **kwargs)
        return EmailStr(value)


class _GCURL(fields.URL):
    def _deserialize(  # type: ignore
        self,
        value: str,
        attr: Optional[str] = None,
        data: Optional[dict] = None,
        **kwargs: Any
    ) -> URLStr:
        value = super()._deserialize(value=value, attr=attr, data=data, **kwargs)
        return URLStr(value)


FIELD_CONVERSION: "OrderedDict[Type[Any], Type[HandlerType]]" = OrderedDict(
    (
        (EmailStr, _GCEmail),
        (URLStr, _GCURL),
        (bool, fields.Bool),
        (str, fields.Str),
        (int, fields.Int),
        (float, fields.Float),
        (list, fields.List),
        (dict, fields.Dict),
        (datetime.datetime, fields.DateTime),
        (datetime.date, fields.Date),
        (datetime.time, fields.Time),
        (datetime.timedelta, fields.TimeDelta),
        (uuid.UUID, fields.UUID),
        (Mapping, fields.Mapping),
        (List, fields.List),
    )
)
