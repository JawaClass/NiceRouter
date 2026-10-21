from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NiceRouterError(Exception):
    """Base class for all errors raised by nicerouter's routing package."""

    status_code: int = 500

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class InvalidQueryError(NiceRouterError):
    """Invalid filter/sort parameters supplied by the client."""

    status_code = 400


class NotFoundError(NiceRouterError):
    status_code = 404


class ConflictError(NiceRouterError):
    status_code = 409


class IntegrityViolationError(NiceRouterError):
    status_code = 400


class DatabaseError(NiceRouterError):
    status_code = 500

