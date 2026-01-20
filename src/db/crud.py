from sqlalchemy.orm import Session

from src.models.job_model import RawJobListing


def insert_raw_job_listing(
    *,
    session: Session,
    job_listing: list[RawJobListing]
):
    session.add_all(job_listing)
    session.commit()
