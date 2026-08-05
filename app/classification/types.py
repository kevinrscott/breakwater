from dataclasses import dataclass
from enum import Enum


class ExperienceRequirementType(str, Enum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"
    NICE_TO_HAVE = "NICE_TO_HAVE"
    FLEXIBLE = "FLEXIBLE"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_FOUND = "NOT_FOUND"


@dataclass(frozen=True, slots=True)
class ExperienceEvidence:
    rule_id: str
    source_field: str
    excerpt: str
    requirement_type: ExperienceRequirementType
    minimum: int | None
    maximum: int | None


@dataclass(frozen=True, slots=True)
class ExperienceClassification:
    years_required_min: int | None
    years_required_max: int | None
    years_preferred: int | None
    requirement_type: ExperienceRequirementType
    evidence: tuple[ExperienceEvidence, ...]
