import pytest
import sqlalchemy as sa

from nicerouter.routing.exceptions import (
    ConflictError,
    InvalidQueryError,
    NotFoundError,
)
from nicerouter.routing.models.models import ResponseType
from nicerouter.routing.service import db_helper, param_builders, service_methods
from nicerouter.routing.service.service_helper import scalar_or_throw
from tests.tests_routing.conftest import Author, Book

pytestmark = pytest.mark.anyio


class TestParamBuilders:
    def test_filter_by_builds_expressions(self):
        filters = param_builders.build_filter_by("pages=100,published=true", Book)
        assert len(filters) == 2

    def test_filter_unknown_field(self):
        with pytest.raises(InvalidQueryError, match="Invalid filter field: nope"):
            param_builders.build_filter_by("nope=1", Book)

    def test_filter_relationship_is_not_a_column(self):
        with pytest.raises(InvalidQueryError):
            param_builders.build_filter_by("author=1", Book)

    def test_filter_bad_cast(self):
        with pytest.raises(InvalidQueryError, match="Cannot cast"):
            param_builders.build_filter_by("pages=abc", Book)

    def test_sort_by_directions(self):
        cols = param_builders.build_sort_by("title,-pages", Book)
        assert len(cols) == 2

    def test_sort_unknown_field(self):
        with pytest.raises(InvalidQueryError, match="Invalid sort field"):
            param_builders.build_sort_by("nope", Book)

    def test_errors_carry_status_code(self):
        assert InvalidQueryError("x").status_code == 400
        assert NotFoundError("x").status_code == 404
        assert ConflictError("x").status_code == 409


class TestCommitDbOps:
    async def test_commits_on_success(self, db, seeded):
        async with db_helper.commit_db_ops(db=db):
            db.add(Author(name="Cy", email="cy@example.com"))

        count = await db.scalar(sa.select(sa.func.count()).select_from(Author))
        assert count == 3

    async def test_unique_violation_rolls_back(self, db, seeded):
        from nicerouter.routing.exceptions import IntegrityViolationError

        with pytest.raises(IntegrityViolationError) as exc:
            async with db_helper.commit_db_ops(db=db):
                db.add(Author(name="Dup", email="alice@example.com"))
        assert exc.value.status_code == 400
        assert "already exists" in exc.value.detail

    async def test_foreign_key_violation_is_conflict(self, db, seeded):
        author = await db.scalar(sa.select(Author).where(Author.name == "Alice"))
        with pytest.raises(ConflictError):
            async with db_helper.commit_db_ops(db=db):
                await db.delete(author)

    async def test_nice_errors_pass_through_and_rollback(self, db, seeded):
        with pytest.raises(NotFoundError):
            async with db_helper.commit_db_ops(db=db):
                db.add(Author(name="Ghost", email="ghost@example.com"))
                raise NotFoundError("boom")

        count = await db.scalar(sa.select(sa.func.count()).select_from(Author))
        assert count == 2

    async def test_unexpected_error_becomes_database_error(self, db, seeded):
        from nicerouter.routing.exceptions import DatabaseError

        with pytest.raises(DatabaseError):
            async with db_helper.commit_db_ops(db=db):
                raise RuntimeError("kaputt")


class TestScalarOrThrow:
    async def test_found(self, db, seeded):
        author = await scalar_or_throw(
            db=db, db_class=Author, query=sa.select(Author).where(Author.id == 1)
        )
        assert author.name == "Alice"

    async def test_missing(self, db, seeded):
        with pytest.raises(NotFoundError, match="Author not found"):
            await scalar_or_throw(
                db=db, db_class=Author, query=sa.select(Author).where(Author.id == 99)
            )


class TestServiceMethods:
    async def test_delete(self, db, seeded):
        res = await service_methods.delete(entity_id=3, db=db, db_class=Book)
        assert res.deleted_id == 3
        assert await db.get(Book, 3) is None

    async def test_delete_missing(self, db, seeded):
        with pytest.raises(NotFoundError):
            await service_methods.delete(entity_id=99, db=db, db_class=Book)

    async def test_delete_referenced_row_conflicts(self, db, seeded):
        with pytest.raises(ConflictError):
            await service_methods.delete(entity_id=1, db=db, db_class=Author)

    async def test_delete_batch(self, db, seeded):
        res = await service_methods.delete_batch(id_list=[1, 2], db=db, db_class=Book)
        assert res.deleted_count == 2

    async def test_delete_batch_reports_missing_ids_and_deletes_nothing(
        self, db, seeded
    ):
        with pytest.raises(NotFoundError, match="99"):
            await service_methods.delete_batch(id_list=[1, 99], db=db, db_class=Book)
        assert await db.get(Book, 1) is not None

    async def test_get_all_filter_and_sort(self, db, seeded):
        from nicerouter.routing.models.model_generator import generate_model_schema_out
        from nicerouter.normalization.type_builder import build_normalized_store_model

        out = generate_model_schema_out(Book)
        rows = await service_methods.get_all(
            db=db,
            db_class=Book,
            response_type=ResponseType.Nested,
            response_model=out,
            normalized_response_model=build_normalized_store_model(out),
            query=None,
            filter_by="published=true",
            sort_by="-pages",
        )
        assert [r["title"] for r in rows] == ["Gamma", "Alpha"]

    async def test_get_all_invalid_filter(self, db, seeded):
        from nicerouter.routing.models.model_generator import generate_model_schema_out
        from nicerouter.normalization.type_builder import build_normalized_store_model

        out = generate_model_schema_out(Book)
        with pytest.raises(InvalidQueryError):
            await service_methods.get_all(
                db=db,
                db_class=Book,
                response_type=ResponseType.Nested,
                response_model=out,
                normalized_response_model=build_normalized_store_model(out),
                query=None,
                filter_by="nope=1",
            )
