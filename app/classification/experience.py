import re
from dataclasses import dataclass

from classification.types import (
    ExperienceClassification,
    ExperienceEvidence,
    ExperienceRequirementType,
)

_SOURCE_FIELD = "description_text"
_FLAGS = re.IGNORECASE | re.VERBOSE
_RANGE_SEPARATOR = r"(?:-|\u2013|to)"
_APOSTROPHE = r"['\u2019]"
_INTEGER_TOKEN = r"(?<![\w.,/])\d+(?![\w.,/])"
_NON_INTEGER_COMPONENT = r"\d+(?:[.,]\d+|/\d+)"
_NON_INTEGER_TOKEN = rf"""
    (?<![\w.,/])
    (?:
        {_NON_INTEGER_COMPONENT}
        (?:\s*{_RANGE_SEPARATOR}\s*(?:{_NON_INTEGER_COMPONENT}|\d+))?
        |
        \d+\s*{_RANGE_SEPARATOR}\s*{_NON_INTEGER_COMPONENT}
    )
    (?![\w.,/])
"""
_EXPERIENCE_WORDING = r"""
    (?:(?!(?:combined|education)\b)[a-z][a-z-]*\s+){0,3}
    experience
"""
_EXPERIENCE_SUFFIX = rf"""
    (?:\s+of\s+|{_APOSTROPHE}s?\s+|\s+)
    {_EXPERIENCE_WORDING}
"""
_QUALIFIER_SEPARATOR = r"[\s,;:()\-]*"
_PREFERRED_QUALIFIER = r"(?:is\s+)?preferred\b"
_FLEXIBLE_NOT_REQUIRED_QUALIFIER = r"""
    (?:is|are)\s+(?:not\s+required|optional|not\s+necessary)\b
"""
_NICE_TO_HAVE_QUALIFIER = r"""
    (?:
        would\s+be\s+an?\s+asset
        |is\s+an?\s+asset
        |(?:is\s+)?nice[\s-]+to[\s-]+have
        |(?:is|would\s+be)\s+an?\s+plus
        |(?:is\s+)?desired
        |(?:is\s+)?desirable
        |(?:is|would\s+be)\s+advantageous
    )\b
"""
_ORGANIZATION_HISTORY_RELATION = re.compile(
    r"""
    \b(?:
        (?:our|the|this)\s+
        (?:
            company|organization|business|founders?|leadership(?:\s+team)?
            |employees?|engineers?|engineering\s+team|team
        )
        (?:\s+collectively)?(?:,\s*who)?\s+
        (?:has|have|brings?|offers?|possesses?|boasts?)
        |
        we\s+(?:collectively\s+)?(?:have|bring|offer|possess|boast)
        |
        founded\s+by\s+
        (?:professionals?|founders?|employees?|engineers?|leaders?)\s+with
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
_RELATION_NUMERIC_LEAD = re.compile(
    r"(?:\s+|(?:a\s+)?combined|more\s+than|at\s+least|over|between|and|"
    r"\d+|[-+\u2013./])*",
    re.IGNORECASE,
)
_SUPPLIED_EXPERIENCE_RELATION = re.compile(
    r"""
    \b(?:
        you\s+(?:will\s+)?gain
        |
        (?:this|the|our)\s+(?:internship|program|role|organization|company)\s+
        (?:provides?|offers?|gives?(?:\s+you)?)
        |
        build
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


@dataclass(frozen=True, slots=True)
class _Rule:
    rule_id: str
    requirement_type: ExperienceRequirementType
    pattern: re.Pattern[str]
    value_kind: str


@dataclass(frozen=True, slots=True)
class _Candidate:
    start: int
    end: int
    priority: int
    evidence: ExperienceEvidence


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, _FLAGS)


_RULES = (
    _Rule(
        "EXP_AMBIGUOUS_NON_INTEGER",
        ExperienceRequirementType.AMBIGUOUS,
        _compile(
            rf"""
            (?P<value>{_NON_INTEGER_TOKEN})\s*\+?\s+years?
            {_EXPERIENCE_SUFFIX}
            """
        ),
        "non_integer",
    ),
    _Rule(
        "EXP_AMBIGUOUS_COMBINED_EDUCATION",
        ExperienceRequirementType.AMBIGUOUS,
        _compile(
            rf"""
            between\s+(?P<minimum>{_INTEGER_TOKEN})\s+and\s+(?P<maximum>{_INTEGER_TOKEN})
            \s+years?\s+(?:of\s+)?
            (?:(?:an?\s+)?(?:equivalent\s+)?combination\s+of|combined\s+)?
            education\s+and\s+(?:professional\s+|relevant\s+|work\s+)?experience
            (?:\s+combined)?
            """
        ),
        "ambiguous",
    ),
    _Rule(
        "EXP_AMBIGUOUS_COMBINED_EDUCATION",
        ExperienceRequirementType.AMBIGUOUS,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})
            (?:\s*{_RANGE_SEPARATOR}\s*(?P<maximum>{_INTEGER_TOKEN}))?
            \s+years?\s+(?:of\s+)?
            (?:(?:an?\s+)?(?:equivalent\s+)?combination\s+of|combined\s+)?
            education\s+and\s+(?:professional\s+|relevant\s+|work\s+)?experience
            (?:\s+combined)?
            """
        ),
        "ambiguous",
    ),
    _Rule(
        "EXP_FLEXIBLE_NOT_REQUIRED",
        ExperienceRequirementType.FLEXIBLE,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s+years?{_EXPERIENCE_SUFFIX}
            {_QUALIFIER_SEPARATOR}{_FLEXIBLE_NOT_REQUIRED_QUALIFIER}
            """
        ),
        "exact",
    ),
    _Rule(
        "EXP_PREFERRED_RANGE",
        ExperienceRequirementType.PREFERRED,
        _compile(
            rf"""
            between\s+(?P<minimum>{_INTEGER_TOKEN})\s+and\s+(?P<maximum>{_INTEGER_TOKEN})
            \s+years?(?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_PREFERRED_QUALIFIER}
            """
        ),
        "range",
    ),
    _Rule(
        "EXP_PREFERRED_RANGE",
        ExperienceRequirementType.PREFERRED,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s*{_RANGE_SEPARATOR}\s*(?P<maximum>{_INTEGER_TOKEN})
            \s+years?(?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_PREFERRED_QUALIFIER}
            """
        ),
        "range",
    ),
    _Rule(
        "EXP_PREFERRED_OPEN_ENDED",
        ExperienceRequirementType.PREFERRED,
        _compile(
            rf"""
            (?:at\s+least|minimum(?:\s+of)?)\s+(?P<minimum>{_INTEGER_TOKEN})
            \s+years?(?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_PREFERRED_QUALIFIER}
            """
        ),
        "open",
    ),
    _Rule(
        "EXP_PREFERRED_OPEN_ENDED",
        ExperienceRequirementType.PREFERRED,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s*(?:\+|\s+or\s+more)\s*years?
            (?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_PREFERRED_QUALIFIER}
            """
        ),
        "open",
    ),
    _Rule(
        "EXP_PREFERRED_EXACT",
        ExperienceRequirementType.PREFERRED,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s+years?(?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_PREFERRED_QUALIFIER}
            """
        ),
        "exact",
    ),
    _Rule(
        "EXP_NICE_TO_HAVE_RANGE",
        ExperienceRequirementType.NICE_TO_HAVE,
        _compile(
            rf"""
            between\s+(?P<minimum>{_INTEGER_TOKEN})\s+and\s+(?P<maximum>{_INTEGER_TOKEN})
            \s+years?(?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_NICE_TO_HAVE_QUALIFIER}
            """
        ),
        "range",
    ),
    _Rule(
        "EXP_NICE_TO_HAVE_RANGE",
        ExperienceRequirementType.NICE_TO_HAVE,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s*{_RANGE_SEPARATOR}\s*(?P<maximum>{_INTEGER_TOKEN})
            \s+years?(?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_NICE_TO_HAVE_QUALIFIER}
            """
        ),
        "range",
    ),
    _Rule(
        "EXP_NICE_TO_HAVE_OPEN_ENDED",
        ExperienceRequirementType.NICE_TO_HAVE,
        _compile(
            rf"""
            (?:at\s+least|minimum(?:\s+of)?)\s+(?P<minimum>{_INTEGER_TOKEN})
            \s+years?(?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_NICE_TO_HAVE_QUALIFIER}
            """
        ),
        "open",
    ),
    _Rule(
        "EXP_NICE_TO_HAVE_OPEN_ENDED",
        ExperienceRequirementType.NICE_TO_HAVE,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s*(?:\+|\s+or\s+more)\s*years?
            (?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_NICE_TO_HAVE_QUALIFIER}
            """
        ),
        "open",
    ),
    _Rule(
        "EXP_NICE_TO_HAVE_EXACT",
        ExperienceRequirementType.NICE_TO_HAVE,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s+years?(?:{_EXPERIENCE_SUFFIX})?
            {_QUALIFIER_SEPARATOR}{_NICE_TO_HAVE_QUALIFIER}
            """
        ),
        "exact",
    ),
    _Rule(
        "EXP_REQUIRED_RANGE",
        ExperienceRequirementType.REQUIRED,
        _compile(
            rf"""
            between\s+(?P<minimum>{_INTEGER_TOKEN})\s+and\s+(?P<maximum>{_INTEGER_TOKEN})
            \s+years?{_EXPERIENCE_SUFFIX}
            (?:{_QUALIFIER_SEPARATOR}(?:is\s+)?required\b)?
            """
        ),
        "range",
    ),
    _Rule(
        "EXP_REQUIRED_RANGE",
        ExperienceRequirementType.REQUIRED,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s*{_RANGE_SEPARATOR}\s*(?P<maximum>{_INTEGER_TOKEN})
            \s+years?{_EXPERIENCE_SUFFIX}
            (?:{_QUALIFIER_SEPARATOR}(?:is\s+)?required\b)?
            """
        ),
        "range",
    ),
    _Rule(
        "EXP_REQUIRED_OPEN_ENDED",
        ExperienceRequirementType.REQUIRED,
        _compile(
            rf"""
            (?:at\s+least|minimum(?:\s+of)?)\s+(?P<minimum>{_INTEGER_TOKEN})
            \s+years?{_EXPERIENCE_SUFFIX}
            (?:{_QUALIFIER_SEPARATOR}(?:is\s+)?required\b)?
            """
        ),
        "open",
    ),
    _Rule(
        "EXP_REQUIRED_OPEN_ENDED",
        ExperienceRequirementType.REQUIRED,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s*(?:\+|\s+or\s+more)\s*years?
            {_EXPERIENCE_SUFFIX}
            (?:{_QUALIFIER_SEPARATOR}(?:is\s+)?required\b)?
            """
        ),
        "open",
    ),
    _Rule(
        "EXP_REQUIRED_OPEN_ENDED",
        ExperienceRequirementType.REQUIRED,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s*(?:\+|\s+or\s+more)\s*years?
            [\s,;:()\-]*(?:is\s+)?required\b
            """
        ),
        "open",
    ),
    _Rule(
        "EXP_REQUIRED_EXACT",
        ExperienceRequirementType.REQUIRED,
        _compile(
            rf"""
            (?P<minimum>{_INTEGER_TOKEN})\s+years?{_EXPERIENCE_SUFFIX}
            (?:{_QUALIFIER_SEPARATOR}(?:is\s+)?required\b)?
            """
        ),
        "exact",
    ),
)

_FLEXIBLE_RULES = (
    _compile(
        r"equivalent\s+(?:professional\s+)?experience\s+"
        r"(?:will|may|can)\s+be\s+considered"
    ),
    _compile(
        r"(?:an?\s+)?degree\s+or\s+(?:an?\s+)?equivalent\s+"
        r"(?:professional\s+)?experience"
    ),
    _compile(
        r"(?:an?\s+)?equivalent\s+combination\s+of\s+education\s+and\s+"
        r"(?:professional\s+)?experience"
    ),
)


def classify_experience(description_text: str) -> ExperienceClassification:
    """Extract professional-experience requirements from normalized plain text."""
    candidates = _collect_candidates(description_text)
    evidence = tuple(
        candidate.evidence
        for candidate in sorted(candidates, key=lambda item: item.start)
    )

    required = [
        item
        for item in evidence
        if item.requirement_type is ExperienceRequirementType.REQUIRED
    ]
    preferred = [
        item
        for item in evidence
        if item.requirement_type is ExperienceRequirementType.PREFERRED
    ]
    nice_to_have = [
        item
        for item in evidence
        if item.requirement_type is ExperienceRequirementType.NICE_TO_HAVE
    ]
    ambiguous = [
        item
        for item in evidence
        if item.requirement_type is ExperienceRequirementType.AMBIGUOUS
    ]

    selected_non_required = preferred or nice_to_have
    strongest_non_required = (
        max(selected_non_required, key=_non_required_value)
        if selected_non_required
        else None
    )
    years_preferred = (
        _non_required_value(strongest_non_required) if strongest_non_required else None
    )

    contradictory_professional_evidence = any(
        item.rule_id == "EXP_AMBIGUOUS_CONTRADICTORY_RANGE" for item in ambiguous
    )

    if required and not contradictory_professional_evidence:
        required_minimum = max(
            item.minimum for item in required if item.minimum is not None
        )
        bounded_maximums = [
            item.maximum for item in required if item.maximum is not None
        ]
        if any(maximum < required_minimum for maximum in bounded_maximums):
            return _result(
                ExperienceRequirementType.AMBIGUOUS,
                years_preferred=years_preferred,
                evidence=evidence,
            )

        required_maximum = (
            None
            if any(item.maximum is None for item in required)
            else min(bounded_maximums)
        )

        return _result(
            ExperienceRequirementType.REQUIRED,
            years_required_min=required_minimum,
            years_required_max=required_maximum,
            years_preferred=years_preferred,
            evidence=evidence,
        )

    if ambiguous or contradictory_professional_evidence:
        return _result(
            ExperienceRequirementType.AMBIGUOUS,
            years_preferred=years_preferred,
            evidence=evidence,
        )

    if strongest_non_required:
        return _result(
            strongest_non_required.requirement_type,
            years_preferred=years_preferred,
            evidence=evidence,
        )

    if evidence:
        return _result(ExperienceRequirementType.FLEXIBLE, evidence=evidence)

    return _result(ExperienceRequirementType.NOT_FOUND)


def _collect_candidates(description_text: str) -> list[_Candidate]:
    if not description_text or not description_text.strip():
        return []

    candidates: list[_Candidate] = []
    for priority, rule in enumerate(_RULES):
        for match in rule.pattern.finditer(description_text):
            if (
                rule.requirement_type is ExperienceRequirementType.REQUIRED
                or rule.rule_id == "EXP_AMBIGUOUS_NON_INTEGER"
            ) and (
                _is_organization_history(description_text, match)
                or _is_supplied_experience(description_text, match)
            ):
                continue

            if rule.value_kind == "non_integer":
                minimum = None
                maximum = None
            else:
                minimum = int(match.group("minimum"))
                maximum_group = match.groupdict().get("maximum")
                maximum = int(maximum_group) if maximum_group else None
            requirement_type = rule.requirement_type
            rule_id = rule.rule_id

            if rule.value_kind == "exact":
                maximum = minimum
            elif rule.value_kind == "open":
                maximum = None
            elif (
                rule.value_kind == "range"
                and minimum is not None
                and maximum is not None
            ):
                if minimum > maximum:
                    requirement_type = ExperienceRequirementType.AMBIGUOUS
                    rule_id = "EXP_AMBIGUOUS_CONTRADICTORY_RANGE"

            candidates.append(
                _Candidate(
                    start=match.start(),
                    end=match.end(),
                    priority=priority,
                    evidence=ExperienceEvidence(
                        rule_id=rule_id,
                        source_field=_SOURCE_FIELD,
                        excerpt=_excerpt(match.group(0)),
                        requirement_type=requirement_type,
                        minimum=minimum,
                        maximum=maximum,
                    ),
                )
            )

    flexible_priority = len(_RULES)
    for pattern in _FLEXIBLE_RULES:
        for match in pattern.finditer(description_text):
            candidates.append(
                _Candidate(
                    start=match.start(),
                    end=match.end(),
                    priority=flexible_priority,
                    evidence=ExperienceEvidence(
                        rule_id="EXP_FLEXIBLE_EQUIVALENT",
                        source_field=_SOURCE_FIELD,
                        excerpt=_excerpt(match.group(0)),
                        requirement_type=ExperienceRequirementType.FLEXIBLE,
                        minimum=None,
                        maximum=None,
                    ),
                )
            )

    accepted: list[_Candidate] = []
    for candidate in sorted(candidates, key=lambda item: (item.priority, item.start)):
        if not any(_overlaps(candidate, existing) for existing in accepted):
            accepted.append(candidate)
    return accepted


def _overlaps(left: _Candidate, right: _Candidate) -> bool:
    return left.start < right.end and right.start < left.end


def _is_organization_history(description_text: str, match: re.Match[str]) -> bool:
    return _has_local_numeric_relation(
        description_text,
        match,
        _ORGANIZATION_HISTORY_RELATION,
    )


def _is_supplied_experience(description_text: str, match: re.Match[str]) -> bool:
    return _has_local_numeric_relation(
        description_text,
        match,
        _SUPPLIED_EXPERIENCE_RELATION,
    )


def _has_local_numeric_relation(
    description_text: str,
    match: re.Match[str],
    relation_pattern: re.Pattern[str],
) -> bool:
    boundary = max(
        description_text.rfind(separator, 0, match.start())
        for separator in (".", "!", "?", ";", "\n")
    )
    local_prefix = description_text[boundary + 1 : match.start()]
    relationships = list(relation_pattern.finditer(local_prefix))
    if not relationships:
        return False
    text_after_relationship = local_prefix[relationships[-1].end() :]
    return bool(_RELATION_NUMERIC_LEAD.fullmatch(text_after_relationship))


def _non_required_value(evidence: ExperienceEvidence) -> int:
    if evidence.maximum is not None:
        return evidence.maximum
    if evidence.minimum is not None:
        return evidence.minimum
    raise ValueError("Non-required numeric evidence must include a numeric value.")


def _excerpt(value: str) -> str:
    return " ".join(value.split())


def _result(
    requirement_type: ExperienceRequirementType,
    *,
    years_required_min: int | None = None,
    years_required_max: int | None = None,
    years_preferred: int | None = None,
    evidence: tuple[ExperienceEvidence, ...] = (),
) -> ExperienceClassification:
    return ExperienceClassification(
        years_required_min=years_required_min,
        years_required_max=years_required_max,
        years_preferred=years_preferred,
        requirement_type=requirement_type,
        evidence=evidence,
    )
