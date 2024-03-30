from __future__ import annotations

from typing import Annotated, Any

from pydantic import AnyHttpUrl, ValidationError, ValidationInfo, ValidatorFunctionWrapHandler, WrapValidator

INVALID_URL_PLACEHOLDER = "original.was.invalid"


def attempt_with_url_placeholder(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> AnyHttpUrl:
    """Wrap validator to replace an invalid URL with a placeholder.

    Some feeds contain the occasional invalid URL that would otherwise break feedparsing
    entirely. If the URL is not needed for archiving, we can tolerate a placeholder.
    """
    try:
        return handler(v)
    except ValidationError:
        return handler("http://" + INVALID_URL_PLACEHOLDER)


LenientUrl = Annotated[AnyHttpUrl, WrapValidator(attempt_with_url_placeholder)]
