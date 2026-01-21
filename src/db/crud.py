from typing import Generator

from sqlalchemy.orm import Session

from src.models.job_model import RawJobListing


def insert_raw_job_listing(
    *,
    session: Session,
    job_listing: list[RawJobListing]
):
    session.add_all(job_listing)
    session.commit()

def select_all_raw_job_listing_ids(
    *,
    session: Session
) -> list[str]:
    return [job.job_id for job in session.query(RawJobListing).all()]
