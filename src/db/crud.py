from collections.abc import Sequence
from typing import TypeVar

from sqlmodel import Session, select
from sqlalchemy.dialects.sqlite import insert

from src.models.job_model import RawJobListing, ProcessedJobListing

T = TypeVar("T", RawJobListing, ProcessedJobListing)

def upsert_job_listing(
    *,
    session: Session,
    model: type[T],
    job_listing: list[T],
):
    if not job_listing:
        return

    values = [obj.model_dump() for obj in job_listing]
    conflict_columns =  ["job_id"]

    stmt = insert(model).values(values)

    update_columns = {
        c.name: getattr(stmt.excluded, c.name)
        for c in model.__table__.columns
        if c.name not in conflict_columns
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns,
        set_=update_columns,
    )

    session.exec(stmt)
    session.commit()


def select_all_raw_job_listing_ids(
    *,
    session: Session
) -> list[str]:
    return [job.job_id for job in session.exec(select(RawJobListing)).fetchall()]


def select_job_listing_to_be_processed_by_llm(
        *,
        session: Session,
) -> Sequence[RawJobListing]:
    return (
        session.exec(
            select(RawJobListing)
            .outerjoin(
                ProcessedJobListing,
                RawJobListing.job_id == ProcessedJobListing.job_id
            )
            .where(
                ProcessedJobListing.job_id == None # noqa: E711
            )
        ).fetchall()
    )
