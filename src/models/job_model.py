import hashlib
from functools import cached_property

from pydantic import BaseModel, computed_field


class RawJobListing(BaseModel):
    title: str
    description: str

    @computed_field
    @cached_property
    def job_id(self) -> str:
        return hashlib.md5(self.title.encode("utf-8")).hexdigest()


class JobListing(BaseModel):
    id: str
    title: str
    description: str
    job_url: str | None = None
    company_url: str | None = None
    technologies: list[str] | None = None
    location: str | None = None
    industry: str | None = None
    salary: str | None = None
    is_remote: bool | None = None
