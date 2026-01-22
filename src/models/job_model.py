import hashlib
from datetime import date
from functools import cached_property

from pydantic import BaseModel, computed_field
from sqlalchemy import Column
from sqlalchemy.dialects.sqlite.json import JSON
from sqlmodel import SQLModel, Field

class HNJobPosting(BaseModel):
    title: str
    description: str
    posted_date: date | None

    @computed_field
    @cached_property
    def job_id(self) -> str:
        if self.posted_date:
            str_date = self.posted_date.isoformat()
        else:
            str_date = ""

        return hashlib.sha256(
            (self.title + str_date).encode("utf-8")
        ).hexdigest()


class JobBase(SQLModel):
    job_id: str
    title: str
    description: str
    posted_date: date | None

    @classmethod
    def of(cls, raw: HNJobPosting):
        return JobBase(
            job_id = raw.job_id,
            title = raw.title,
            description = raw.description,
            posted_date = raw.posted_date,
        )

class RawJob(JobBase, table=True):

    __tablename__ = "raw_jobs"

    job_id: str = Field(primary_key=True, nullable=False)


class ProcessedJobs(JobBase, table=True):

    __tablename__ = "processed_jobs"

    job_id: str = Field(primary_key=True, nullable=False)

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
