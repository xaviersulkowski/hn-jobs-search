import hashlib
from datetime import date
from typing import Any

from sqlalchemy import Column
from sqlalchemy.dialects.sqlite.json import JSON
from sqlmodel import SQLModel, Field


class JobBase(SQLModel):
    title: str
    description: str
    posted_date: date | None

    def hash(self):
        if self.posted_date:
            str_date = self.posted_date.isoformat()
        else: str_date = ""

        return hashlib.sha256(
            (self.title + str_date).encode("utf-8")
        ).hexdigest()

class RawJobListing(JobBase, table=True):

    __tablename__ = "raw_job_listing"

    job_id: str = Field(primary_key=True)

    def model_post_init(self, context: Any, /) -> None:
        self.job_id = self.hash()


class ProcessedJobListing(JobBase, table=True):

    __tablename__ = "processed_job_listing"

    job_id: str = Field(primary_key=True)

    job_url: str | None = Field(default=None)
    company_url: str | None = Field(default=None)
    technologies: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON)
    )
    location: str | None = Field(default=None)
    industry: str | None = Field(default=None)
    salary: str | None = Field(default=None)
    is_remote: bool | None = Field(default=None)

    def model_post_init(self, context: Any, /) -> None:
        self.job_id = self.hash()
