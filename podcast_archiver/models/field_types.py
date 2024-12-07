from __future__ import annotations

from contextlib import suppress
from datetime import datetime
from time import mktime, struct_time
from typing import Annotated, Any

from pydantic import (
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)
from pydantic.functional_validators import BeforeValidator

from podcast_archiver import compat


def parse_from_struct_time(value: struct_time | datetime) -> datetime:
    if isinstance(value, struct_time):
        value = datetime.fromtimestamp(mktime(value))
    if not value.tzinfo:
        value = value.replace(tzinfo=compat.UTC)
    return value


def val_or_none(value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
    with suppress(ValidationError):
        return handler(value)
    return None


FallbackToNone = WrapValidator(val_or_none)
LenientDatetime = Annotated[datetime, BeforeValidator(parse_from_struct_time)]
LenientInt = Annotated[int | None, FallbackToNone]
