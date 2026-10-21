from contextlib import asynccontextmanager
from nicerouter.routing.exceptions import (
    ConflictError,
    DatabaseError,
    IntegrityViolationError,
    NiceRouterError,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def commit_db_ops(db: AsyncSession):
    try:
        yield
        await db.commit()
    except NiceRouterError:
        # Already one of our errors (like NotFoundError), pass it through.
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        err_msg = str(e.orig).lower()
        if "foreign key" in err_msg or "violates foreign key" in err_msg:
            detail = "Action failed: This record is still referenced by other data."
            raise ConflictError(detail) from e
        elif "unique" in err_msg or "already exists" in err_msg:
            detail = "Action failed: A record with this value already exists."
            raise IntegrityViolationError(detail) from e
        else:
            detail = "Database integrity violation."
        raise IntegrityViolationError(detail) from e
    except Exception as e:
        await db.rollback()
        raise DatabaseError(f"An unexpected database error occurred. {e=}") from e
