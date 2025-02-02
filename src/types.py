from typing import Any, TypedDict

from pydantic import BaseModel


class ScrapeEndpointJsonSchema(TypedDict):
    metadata: Any
    json: Any


class ExtractEndpointSchema(TypedDict):
    success: bool
    data: Any
    status: str
    expiresAt: str


class ApplyLinksSchema(BaseModel):
    apply_links: list[str]


class JobSchema(BaseModel):
    job_title: str
    sub_division_of_organization: str
    key_skills: list[str]
    compensation: str
    location: str
    apply_link: str


class JobSchemas(BaseModel):
    jobs: list[JobSchema]
