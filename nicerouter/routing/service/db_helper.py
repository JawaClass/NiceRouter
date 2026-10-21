from contextlib import asynccontextmanager
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def commit_db_ops(db: AsyncSession):
    try:
        yield
        await db.commit()
    except HTTPException:
        # If it's already a FastAPI HTTPException (like 404),
        # just let it fly out to the client.
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        err_msg = str(e.orig).lower()
        if "foreign key" in err_msg or "violates foreign key" in err_msg:
            detail = "Action failed: This record is still referenced by other data."
            status_code = status.HTTP_409_CONFLICT
        elif "unique" in err_msg or "already exists" in err_msg:
            detail = "Action failed: A record with this value already exists."
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            detail = "Database integrity violation."
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected database error occurred. {e=}",
        )
