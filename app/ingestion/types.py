from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeAlias

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
RawJob: TypeAlias = Mapping[str, JSONValue]


@dataclass(frozen=True, slots=True)
class NormalizedJobInput:
    """Source-independent fields produced by payload normalization."""

    source_job_id: str
    title: str
    company_name: str
    source_url: str
    application_url: str
    location_text: str
    country_evidence: str | None
    workplace_evidence: str | None
    description_text: str
    raw_payload: RawJob
