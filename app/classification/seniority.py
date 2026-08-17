import re
from dataclasses import dataclass

from classification.types import (
    SeniorityClassification,
    SeniorityEvidence,
    SenioritySignalStrength,
)

_TITLE_SOURCE_FIELD = "title"
_DESCRIPTION_SOURCE_FIELD = "description_text"
_FLAGS = re.IGNORECASE | re.VERBOSE
_HORIZONTAL_SPACE = r"[^\S\r\n]"
_OTHER_PARTY_ACTOR = rf"""
    (?:
        we
        |
        (?:
            (?:(?:the|our|your|their|another|an?){_HORIZONTAL_SPACE}+)?
            (?:
                companies|company|organizations?|business(?:es)?|employers?
                |
                cto|chief{_HORIZONTAL_SPACE}+technology{_HORIZONTAL_SPACE}+officer
                |
                (?:(?:senior|staff|principal|lead){_HORIZONTAL_SPACE}+)?
                    (?:engineers?|developers?|architects?)
                |
                (?:(?:engineering|software|technical|people|hiring)
                    {_HORIZONTAL_SPACE}+)?managers?
                |
                directors?(?:{_HORIZONTAL_SPACE}+of{_HORIZONTAL_SPACE}+
                    (?:engineering|software|technology|development))?
                |
                heads?(?:{_HORIZONTAL_SPACE}+of{_HORIZONTAL_SPACE}+
                    (?:engineering|software|technology|development))?
                |
                leads?|leadership(?:{_HORIZONTAL_SPACE}+team)?
                |management(?:{_HORIZONTAL_SPACE}+team)?|teams?
            )
        )
    )
"""
_OTHER_PARTY_SUBJECT = re.compile(
    rf"""
    \b{_OTHER_PARTY_ACTOR}
    (?:{_HORIZONTAL_SPACE}*,?{_HORIZONTAL_SPACE}*(?:who|that))?
    {_HORIZONTAL_SPACE}+
    (?:
        (?:will|would|can|must|also){_HORIZONTAL_SPACE}+
        |
        (?:is|are|was|were){_HORIZONTAL_SPACE}+
            (?:
                (?:expected{_HORIZONTAL_SPACE}+to
                    |responsible{_HORIZONTAL_SPACE}+for)
                {_HORIZONTAL_SPACE}+
            )?
    )?
    $
    """,
    _FLAGS,
)
_OTHER_PARTY_INFINITIVE = re.compile(
    rf"""
    \b(?:allows?|enables?|helps?|for){_HORIZONTAL_SPACE}+
    {_OTHER_PARTY_ACTOR}{_HORIZONTAL_SPACE}+to{_HORIZONTAL_SPACE}+$
    """,
    _FLAGS,
)


@dataclass(frozen=True, slots=True)
class _Rule:
    rule_id: str
    source_field: str
    strength: SenioritySignalStrength
    pattern: re.Pattern[str]


@dataclass(frozen=True, slots=True)
class _Candidate:
    start: int
    end: int
    priority: int
    evidence: SeniorityEvidence


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, _FLAGS)


_TITLE_SEPARATOR = r"[\s,/\-]+"
_TITLE_MODIFIER = r"""
    (?:
        \.net|application|automation|backend|c\#|c\+\+|cloud|customer|data|development|devops
        |engineering|enterprise|frontend|full[\s-]*stack|implementation
        |integration|it|java|javascript|mobile|operations|platform|product|python
        |qa|quality|security|software|solution|solutions|support|systems?|tech
        |technical|technology|typescript|web|wordpress
    )
"""
_TITLE_ROLE = r"""
    (?:
        administrator|analyst|architect|consultant|developer|director|engineer
        |manager|specialist|writer
    )
"""
_MANAGEMENT_AREA = r"""
    (?:
        administration|application[\s-]+support|customer[\s-]+support
        |data[\s-]+operations|development|engineering|hiring|implementation|it
        |people|product|program|project|qa|quality[\s-]+assurance|software
        |software[\s-]+development|technical[\s-]+support|technology
    )
"""
_TITLE_TRAILING_CONTEXT = r"(?:\s+(?:i|ii|iii|iv)\b)?(?:\s*(?:[,(/\-].*)?)?"
_LEVELED_TITLE_ROLE = rf"""
    (?:
        (?:{_TITLE_MODIFIER}{_TITLE_SEPARATOR}){{0,3}}
            (?:administrator|analyst|architect|consultant|developer|engineer|specialist)
        |
        (?:{_TITLE_MODIFIER}{_TITLE_SEPARATOR}){{1,3}}writer
    )
"""
_LEAD_TITLE_BODY = rf"""
    (?:
        lead{_TITLE_SEPARATOR}{_LEVELED_TITLE_ROLE}
        |
        (?:{_TITLE_MODIFIER}{_TITLE_SEPARATOR}){{1,3}}lead
        |
        (?:{_TITLE_MODIFIER}{_TITLE_SEPARATOR}){{0,3}}
            team{_TITLE_SEPARATOR}lead
    )
"""

_TEAM_DESCRIPTOR = r"(?:cross[\s-]+functional|engineering|interdisciplinary)"


_TITLE_RULES = (
    _Rule(
        "SENIORITY_TITLE_SENIOR",
        _TITLE_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(r"\b(?:senior|sr\.?)(?=\s|$|[,/()\-])"),
    ),
    _Rule(
        "SENIORITY_TITLE_STAFF",
        _TITLE_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(r"\bstaff\b"),
    ),
    _Rule(
        "SENIORITY_TITLE_PRINCIPAL",
        _TITLE_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(r"\bprincipal\b"),
    ),
    _Rule(
        "SENIORITY_TITLE_ARCHITECT",
        _TITLE_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(r"\barchitect\b"),
    ),
    _Rule(
        "SENIORITY_TITLE_LEAD",
        _TITLE_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(rf"\b{_LEAD_TITLE_BODY}\b"),
    ),
    _Rule(
        "SENIORITY_TITLE_MANAGEMENT",
        _TITLE_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(r"\b(?:manager|director)\b|\bhead[\s-]+of\b"),
    ),
)

_TITLE_CONTEXTS = {
    "SENIORITY_TITLE_SENIOR": _compile(
        rf"""
        ^\s*(?:senior|sr\.?)
        {_TITLE_SEPARATOR}(?:{_TITLE_MODIFIER}{_TITLE_SEPARATOR}){{0,3}}
        {_TITLE_ROLE}\b{_TITLE_TRAILING_CONTEXT}$
        """
    ),
    "SENIORITY_TITLE_STAFF": _compile(
        rf"""
        ^\s*staff{_TITLE_SEPARATOR}
        {_LEVELED_TITLE_ROLE}\b{_TITLE_TRAILING_CONTEXT}$
        """
    ),
    "SENIORITY_TITLE_PRINCIPAL": _compile(
        rf"""
        ^\s*principal{_TITLE_SEPARATOR}
        {_LEVELED_TITLE_ROLE}\b{_TITLE_TRAILING_CONTEXT}$
        """
    ),
    "SENIORITY_TITLE_ARCHITECT": _compile(
        rf"""
        ^\s*(?:{_TITLE_MODIFIER}{_TITLE_SEPARATOR}){{0,3}}
        architect\b{_TITLE_TRAILING_CONTEXT}$
        """
    ),
    "SENIORITY_TITLE_LEAD": _compile(
        rf"""
        ^\s*{_LEAD_TITLE_BODY}\b{_TITLE_TRAILING_CONTEXT}$
        """
    ),
    "SENIORITY_TITLE_MANAGEMENT": _compile(
        rf"""
        ^\s*(?:
            (?:senior{_TITLE_SEPARATOR})?
                {_MANAGEMENT_AREA}{_TITLE_SEPARATOR}(?:manager|director)
            |
            (?:manager|director){_TITLE_SEPARATOR}of{_TITLE_SEPARATOR}
                {_MANAGEMENT_AREA}
            |
            (?:manager|director)\s*[,/\-]\s*{_MANAGEMENT_AREA}
            |
            head[\s-]+of{_TITLE_SEPARATOR}{_MANAGEMENT_AREA}
            |
            manager|director
        )\b{_TITLE_TRAILING_CONTEXT}$
        """
    ),
}

_DESCRIPTION_RULES = (
    _Rule(
        "SENIORITY_RESPONSIBILITY_TEAM_MANAGEMENT",
        _DESCRIPTION_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(
            rf"""
            \b(?:
                manag(?:e|es|ing)\s+
                    (?:an?\s+|the\s+)(?:{_TEAM_DESCRIPTOR}\s+)?team
                    (?=
                        \s+of\s+(?:\d+\s+)?
                            (?:engineers?|developers?|employees?|people)
                        |
                        \s+and\s+(?:coach|develop|grow|hire|mentor|support)
                        |
                        \s*(?:[.;,!?•]|\n|$)
                    )
                |
                people[\s-]+manag(?:e|er|ement)\s+(?:for|of)\s+
                    (?:an?\s+|the\s+)?(?:team|engineers?|developers?)
                |
                (?:manage|managing)\s+(?:\d+\s+)?direct\s+reports?
            )\b
            """
        ),
    ),
    _Rule(
        "SENIORITY_RESPONSIBILITY_PERFORMANCE_MANAGEMENT",
        _DESCRIPTION_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(
            r"""
            \b(?:
                (?:
                    own|owns|owning|oversee|oversees|overseeing|lead|leads|leading
                    |manage|manages|managing|responsible\s+for
                )\s+(?:employee\s+)?performance[\s-]+management
                    (?=
                        \s*(?:[.;,!?•]|\n|$)
                        |
                        \s+(?:for|of)\s+(?:the\s+)?
                            (?:team|engineers?|developers?|employees?|people)
                        |
                        \s+across\s+(?:the\s+)?
                            (?:team|organization|organisation|company)
                        |
                        \s+and\s+(?:employee|people|team)\b
                    )
                |
                (?:conduct|conducting|deliver|delivering|own|owning|manage|managing)
                    \s+(?:employee\s+)?performance\s+reviews?
                |
                manag(?:e|es|ing)\s+(?:the\s+)?performance\s+of\s+
                    (?:engineers?|developers?|employees?|team\s+members?)
            )\b
            """
        ),
    ),
    _Rule(
        "SENIORITY_RESPONSIBILITY_HIRING",
        _DESCRIPTION_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(
            r"""
            \b(?:
                hir(?:e|es)\s+(?:and\s+onboard(?:ing)?\s+)?
                    (?:new\s+)?(?:engineers?|developers?|team\s+members?)
                |
                you\s+will\s+be\s+hiring\s+
                    (?:new\s+)?(?:engineers?|developers?|team\s+members?)
                |
                (?:responsible\s+for|own|owns|owning|lead|leads|leading|manage|managing)
                    \s+(?:the\s+)?hiring(?:\s+process)?
            )\b
            """
        ),
    ),
    _Rule(
        "SENIORITY_RESPONSIBILITY_ORG_STRATEGY",
        _DESCRIPTION_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(
            r"""
            \b(?:set|sets|setting|define|defines|defining|own|owns|owning)
                \s+(?:the\s+)?(?:organization|organisation|company|department)
                [\s-]+wide\s+(?:engineering\s+|technical\s+|technology\s+)?strategy\b
            """
        ),
    ),
    _Rule(
        "SENIORITY_RESPONSIBILITY_ENGINEERING_STANDARDS",
        _DESCRIPTION_SOURCE_FIELD,
        SenioritySignalStrength.STRONG,
        _compile(
            r"""
            \b(?:
                (?:own|owns|owning)\s+(?:the\s+)?
                    (?:
                        organization[\s-]+wide\s+|organisation[\s-]+wide\s+
                        |company[\s-]+wide\s+
                    )?
                    engineering\s+standards
                |
                (?:
                    set|sets|setting|define|defines|defining
                    |establish|establishes|establishing
                )\s+(?:the\s+)?
                    (?:
                        organization[\s-]+wide|organisation[\s-]+wide
                        |company[\s-]+wide
                    )\s+engineering\s+standards
            )\b
            """
        ),
    ),
    _Rule(
        "SENIORITY_SUPPORT_MENTORING",
        _DESCRIPTION_SOURCE_FIELD,
        SenioritySignalStrength.SUPPORTING,
        _compile(
            r"""
            \bmentor(?:s|ed|ing)?\s+
                (?:junior|less[\s-]+experienced|early[\s-]+career)
                \s+(?:engineers?|developers?|team\s+members?)\b
            """
        ),
    ),
)


def classify_seniority(
    title: str,
    description_text: str,
) -> SeniorityClassification:
    """Detect strong and supporting seniority signals in normalized job text."""
    candidates = _collect_candidates(title, _TITLE_RULES)
    candidates.extend(_collect_candidates(description_text, _DESCRIPTION_RULES))
    evidence = tuple(
        candidate.evidence
        for candidate in sorted(
            candidates,
            key=lambda item: (
                0 if item.evidence.source_field == _TITLE_SOURCE_FIELD else 1,
                item.start,
                item.priority,
            ),
        )
    )
    return SeniorityClassification(
        has_strong_signal=any(
            item.strength is SenioritySignalStrength.STRONG for item in evidence
        ),
        evidence=evidence,
    )


def _collect_candidates(text: str, rules: tuple[_Rule, ...]) -> list[_Candidate]:
    if not text or not text.strip():
        return []

    candidates: list[_Candidate] = []
    for priority, rule in enumerate(rules):
        for match in rule.pattern.finditer(text):
            if rule.source_field == _TITLE_SOURCE_FIELD and not _has_title_context(
                text, rule
            ):
                continue
            if (
                rule.source_field == _DESCRIPTION_SOURCE_FIELD
                and _belongs_to_other_party(text, match)
            ):
                continue
            candidates.append(
                _Candidate(
                    start=match.start(),
                    end=match.end(),
                    priority=priority,
                    evidence=SeniorityEvidence(
                        rule_id=rule.rule_id,
                        source_field=rule.source_field,
                        excerpt=_excerpt(match.group(0)),
                        strength=rule.strength,
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


def _has_title_context(title: str, rule: _Rule) -> bool:
    pattern = _TITLE_CONTEXTS.get(rule.rule_id)
    return pattern is None or bool(pattern.fullmatch(title))


def _belongs_to_other_party(text: str, match: re.Match[str]) -> bool:
    prefix = text[: match.start()]
    return bool(
        _OTHER_PARTY_SUBJECT.search(prefix) or _OTHER_PARTY_INFINITIVE.search(prefix)
    )


def _excerpt(value: str) -> str:
    return " ".join(value.split())
