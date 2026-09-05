"""Shared V1 error envelope helpers (OpenAPI ErrorEnvelope)."""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse

SCHEMA_VERSION = "v1"


def error_body(
    *,
    code: str,
    message: str,
    retryable: bool = False,
    field_errors: list[dict[str, Any]] | None = None,
    required_facts: list[str] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "retryable": retryable,
    }
    if field_errors:
        error["field_errors"] = field_errors
    if required_facts:
        error["required_facts"] = required_facts
    return {"schema_version": SCHEMA_VERSION, "error": error}


def error_response(
    status_code: int,
    *,
    code: str,
    message: str,
    retryable: bool = False,
    field_errors: list[dict[str, Any]] | None = None,
    required_facts: list[str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(
            code=code,
            message=message,
            retryable=retryable,
            field_errors=field_errors,
            required_facts=required_facts,
        ),
    )


class V1HTTPException(HTTPException):
    """HTTPException that carries an OpenAPI-shaped error payload."""

    def __init__(
        self,
        status_code: int,
        *,
        code: str,
        message: str,
        retryable: bool = False,
        field_errors: list[dict[str, Any]] | None = None,
        required_facts: list[str] | None = None,
    ):
        detail = error_body(
            code=code,
            message=message,
            retryable=retryable,
            field_errors=field_errors,
            required_facts=required_facts,
        )
        super().__init__(status_code=status_code, detail=detail)
