import hashlib
from functools import cached_property

from pydantic import BaseModel, computed_field


class JobListing(BaseModel):
    title: str
    description: str
    website: str | None = None
    tech: str | None = None
    location: list[str] | None = None
    pay_range: str | None = None

    @computed_field
    @cached_property
    def job_id(self) -> str:
        return hashlib.md5(self.title.encode("utf-8")).hexdigest()

