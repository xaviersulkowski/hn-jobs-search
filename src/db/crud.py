import logging
from collections.abc import Sequence
from typing import TypeVar

from sqlmodel import Session, select
from sqlalchemy.dialects.sqlite import insert

from src.models.job_model import RawJob, ProcessedJobs

T = TypeVar("T", RawJob, ProcessedJobs)

def upsert_jobs(
    *,
    session: Session,
    model: type[T],
    job_listing: list[T],
    force: bool = False,
):
    if not job_listing:
        return

    values = [obj.model_dump() for obj in job_listing]
    pk_columns =  ["job_id"]

    stmt = insert(model).values(values)

    if not force:
        logging.info(f"Running without force mode. Conflicts will be ignored.")
        stmt = stmt.on_conflict_do_nothing(
            index_elements=pk_columns,
        )
    else:
        logging.info(f"Running with force mode. Conflicting rows will be updated.")
        update_columns = {
            c.name: getattr(stmt.excluded, c.name)
            for c in model.__table__.columns
            if c.name not in pk_columns
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=pk_columns,
            set_=update_columns,
        )

    session.exec(stmt)
    session.commit()


def select_not_processed_jobs(
    *,
    session: Session,
) -> Sequence[RawJob]:
    return (
        session.exec(
            select(RawJob)
            .outerjoin(
                ProcessedJobs,
                RawJob.job_id == ProcessedJobs.job_id
            )
            .where(
                ProcessedJobs.job_id == None # noqa: E711
            )
        ).fetchall()
    )
