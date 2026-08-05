from dataclasses import FrozenInstanceError

import pytest

from classification import classify_experience
from classification.types import ExperienceRequirementType


@pytest.mark.parametrize(
    ("text", "minimum", "maximum"),
    [
        ("1 year of experience", 1, 1),
        ("2 years of professional experience required", 2, 2),
        ("minimum 3 years of software-development experience", 3, None),
    ],
)
def test_extracts_exact_required_years(text, minimum, maximum):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == minimum
    assert result.years_required_max == maximum
    assert result.evidence[0].rule_id in {
        "EXP_REQUIRED_EXACT",
        "EXP_REQUIRED_OPEN_ENDED",
    }


@pytest.mark.parametrize(
    "text",
    [
        "1-2 years of experience",
        "1–2 years of professional experience",
        "between 1 and 2 years of relevant experience",
        "1 to 2 years of industry experience",
    ],
)
def test_extracts_required_ranges(text):
    result = classify_experience(text)

    assert result.years_required_min == 1
    assert result.years_required_max == 2
    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.evidence[0].rule_id == "EXP_REQUIRED_RANGE"


@pytest.mark.parametrize(
    "text",
    [
        "1+ years of experience",
        "at least 1 year of professional experience",
        "1 or more years of experience",
    ],
)
def test_extracts_open_ended_required_years(text):
    result = classify_experience(text)

    assert result.years_required_min == 1
    assert result.years_required_max is None
    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.evidence[0].rule_id == "EXP_REQUIRED_OPEN_ENDED"


@pytest.mark.parametrize(
    "text",
    [
        "3 years' experience",
        "3 years’ experience",
    ],
)
def test_extracts_exact_apostrophe_experience(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == 3
    assert result.years_required_max == 3
    assert result.evidence[0].rule_id == "EXP_REQUIRED_EXACT"


@pytest.mark.parametrize(
    ("text", "minimum"),
    [
        ("2+ years' professional experience", 2),
        ("2+ years’ professional experience", 2),
        ("at least 1 year's experience", 1),
        ("at least 1 year’s experience", 1),
    ],
)
def test_extracts_open_ended_apostrophe_experience(text, minimum):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == minimum
    assert result.years_required_max is None
    assert result.evidence[0].rule_id == "EXP_REQUIRED_OPEN_ENDED"


@pytest.mark.parametrize(
    "text",
    [
        "1.5 years of experience",
        "2.5+ years of professional experience",
        "1/2 years of experience",
        "1,000 years of experience",
        "10,000 years of professional experience",
        "1,5 years of experience",
        "1/2-1 years of experience",
        "1.5-2.5 years of experience",
    ],
)
def test_non_integer_professional_requirements_are_ambiguous(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.AMBIGUOUS
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert len(result.evidence) == 1
    assert result.evidence[0].rule_id == "EXP_AMBIGUOUS_NON_INTEGER"
    assert result.evidence[0].minimum is None
    assert result.evidence[0].maximum is None
    assert text.split()[0] in result.evidence[0].excerpt


@pytest.mark.parametrize(
    "text",
    [
        "2 years preferred",
        "3 years of experience is preferred",
    ],
)
def test_extracts_preferred_years(text):
    result = classify_experience(text)

    expected = int(text[0])
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert result.years_preferred == expected
    assert result.requirement_type is ExperienceRequirementType.PREFERRED
    assert result.evidence[0].rule_id == "EXP_PREFERRED_EXACT"


@pytest.mark.parametrize(
    "text",
    [
        "1 year would be an asset",
        "2 years is nice to have",
        "3 years nice-to-have",
    ],
)
def test_extracts_nice_to_have_years(text):
    result = classify_experience(text)

    assert result.years_preferred == int(text[0])
    assert result.requirement_type is ExperienceRequirementType.NICE_TO_HAVE
    assert result.evidence[0].rule_id == "EXP_NICE_TO_HAVE_EXACT"


@pytest.mark.parametrize(
    "text",
    [
        "2 years of experience is a plus",
        "2 years of experience would be a plus",
        "2 years of experience desired",
        "2 years of experience is desired",
        "2 years of experience is desirable",
        "2 years of experience would be advantageous",
    ],
)
def test_common_non_required_qualifiers_are_nice_to_have(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.NICE_TO_HAVE
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert result.years_preferred == 2
    assert len(result.evidence) == 1
    assert result.evidence[0].rule_id == "EXP_NICE_TO_HAVE_EXACT"
    assert result.evidence[0].minimum == 2
    assert result.evidence[0].maximum == 2


@pytest.mark.parametrize(
    ("text", "top_level", "rule_id", "minimum", "maximum"),
    [
        ("2-3 years of experience desired", 3, "EXP_NICE_TO_HAVE_RANGE", 2, 3),
        (
            "2+ years of experience would be advantageous",
            2,
            "EXP_NICE_TO_HAVE_OPEN_ENDED",
            2,
            None,
        ),
        (
            "at least 2 years of experience is a plus",
            2,
            "EXP_NICE_TO_HAVE_OPEN_ENDED",
            2,
            None,
        ),
    ],
)
def test_common_non_required_qualifiers_support_ranges_and_open_ended_values(
    text,
    top_level,
    rule_id,
    minimum,
    maximum,
):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.NICE_TO_HAVE
    assert result.years_preferred == top_level
    assert result.evidence[0].rule_id == rule_id
    assert result.evidence[0].minimum == minimum
    assert result.evidence[0].maximum == maximum


@pytest.mark.parametrize(
    ("text", "requirement_type", "minimum", "maximum", "top_level", "rule_id"),
    [
        (
            "2–3 years of experience preferred",
            ExperienceRequirementType.PREFERRED,
            2,
            3,
            3,
            "EXP_PREFERRED_RANGE",
        ),
        (
            "2+ years of experience preferred",
            ExperienceRequirementType.PREFERRED,
            2,
            None,
            2,
            "EXP_PREFERRED_OPEN_ENDED",
        ),
        (
            "at least 2 years of experience preferred",
            ExperienceRequirementType.PREFERRED,
            2,
            None,
            2,
            "EXP_PREFERRED_OPEN_ENDED",
        ),
        (
            "2 or more years of experience preferred",
            ExperienceRequirementType.PREFERRED,
            2,
            None,
            2,
            "EXP_PREFERRED_OPEN_ENDED",
        ),
        (
            "2–3 years of experience would be an asset",
            ExperienceRequirementType.NICE_TO_HAVE,
            2,
            3,
            3,
            "EXP_NICE_TO_HAVE_RANGE",
        ),
        (
            "2+ years of experience is nice to have",
            ExperienceRequirementType.NICE_TO_HAVE,
            2,
            None,
            2,
            "EXP_NICE_TO_HAVE_OPEN_ENDED",
        ),
        (
            "at least 2 years of experience would be an asset",
            ExperienceRequirementType.NICE_TO_HAVE,
            2,
            None,
            2,
            "EXP_NICE_TO_HAVE_OPEN_ENDED",
        ),
    ],
)
def test_non_required_ranges_and_open_ended_signals(
    text,
    requirement_type,
    minimum,
    maximum,
    top_level,
    rule_id,
):
    result = classify_experience(text)

    assert result.requirement_type is requirement_type
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert result.years_preferred == top_level
    assert len(result.evidence) == 1
    assert result.evidence[0].rule_id == rule_id
    assert result.evidence[0].requirement_type is requirement_type
    assert result.evidence[0].minimum == minimum
    assert result.evidence[0].maximum == maximum


def test_explicit_preferred_evidence_outranks_larger_nice_to_have_signal():
    result = classify_experience(
        "2 years of experience is preferred; 4 years would be an asset."
    )

    assert result.years_preferred == 2
    assert result.requirement_type is ExperienceRequirementType.PREFERRED
    assert len(result.evidence) == 2


def test_preferred_evidence_outranks_larger_desirable_signal():
    result = classify_experience(
        "2 years of experience preferred; 4 years of experience is desirable."
    )

    assert result.years_preferred == 2
    assert result.requirement_type is ExperienceRequirementType.PREFERRED
    assert len(result.evidence) == 2


def test_preferred_qualifier_wins_when_non_required_years_are_equal():
    result = classify_experience(
        "3 years would be an asset; 3 years of experience is preferred."
    )

    assert result.years_preferred == 3
    assert result.requirement_type is ExperienceRequirementType.PREFERRED


def test_keeps_required_and_preferred_evidence_separate():
    result = classify_experience(
        "1 year of professional experience required. "
        "3 years of experience is preferred."
    )

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == 1
    assert result.years_required_max == 1
    assert result.years_preferred == 3
    assert [item.rule_id for item in result.evidence] == [
        "EXP_REQUIRED_EXACT",
        "EXP_PREFERRED_EXACT",
    ]


def test_aggregates_multiple_required_signals_deterministically():
    result = classify_experience(
        "1-4 years of professional experience required. "
        "3 years of software-development experience required."
    )

    assert result.years_required_min == 3
    assert result.years_required_max == 3
    assert len(result.evidence) == 2


def test_contradictory_required_signals_are_ambiguous():
    result = classify_experience(
        "1–2 years of experience required. 3 years of experience required."
    )

    assert result.requirement_type is ExperienceRequirementType.AMBIGUOUS
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert len(result.evidence) == 2


def test_any_open_ended_required_signal_keeps_maximum_unbounded():
    result = classify_experience(
        "2-4 years of professional experience and 3+ years of Python experience."
    )

    assert result.years_required_min == 3
    assert result.years_required_max is None


@pytest.mark.parametrize(
    "text",
    [
        "equivalent experience will be considered",
        "a degree or equivalent professional experience",
        "an equivalent combination of education and experience",
    ],
)
def test_recognizes_flexible_equivalent_experience(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.FLEXIBLE
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert result.evidence[0].rule_id == "EXP_FLEXIBLE_EQUIVALENT"


@pytest.mark.parametrize(
    "text",
    [
        "2 years of experience are not required.",
        "2 years of experience is not required.",
        "2 years of experience is optional.",
        "2 years of experience is not necessary.",
    ],
)
def test_negated_or_optional_experience_is_flexible(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.FLEXIBLE
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert result.years_preferred is None
    assert len(result.evidence) == 1
    assert result.evidence[0].rule_id == "EXP_FLEXIBLE_NOT_REQUIRED"
    assert result.evidence[0].minimum == 2
    assert result.evidence[0].maximum == 2


def test_positive_required_wording_remains_required():
    result = classify_experience("2 years of experience is required.")

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == 2
    assert result.years_required_max == 2


def test_combined_education_and_experience_is_ambiguous():
    result = classify_experience("5 years of combined education and experience")

    assert result.requirement_type is ExperienceRequirementType.AMBIGUOUS
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert result.evidence[0].rule_id == "EXP_AMBIGUOUS_COMBINED_EDUCATION"


def test_combined_education_and_experience_range_is_ambiguous():
    result = classify_experience(
        "Between 2 and 3 years of combined education and relevant experience"
    )

    assert result.requirement_type is ExperienceRequirementType.AMBIGUOUS
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert result.evidence[0].minimum == 2
    assert result.evidence[0].maximum == 3


def test_ambiguous_required_total_preserves_clear_preferred_years():
    result = classify_experience(
        "5 years of combined education and experience; 2 years preferred."
    )

    assert result.requirement_type is ExperienceRequirementType.AMBIGUOUS
    assert result.years_preferred == 2
    assert len(result.evidence) == 2


def test_clear_required_signal_resolves_separate_combined_education_ambiguity():
    result = classify_experience(
        "5 years of combined education and experience. "
        "1 year of professional experience required."
    )

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == 1
    assert result.years_required_max == 1
    assert len(result.evidence) == 2
    assert {item.requirement_type for item in result.evidence} == {
        ExperienceRequirementType.AMBIGUOUS,
        ExperienceRequirementType.REQUIRED,
    }


@pytest.mark.parametrize(
    "text",
    [
        "Our leadership team has 20 years of industry experience.",
        "Our founders have more than 15 years of professional experience.",
        "The company brings 10 years of software-development experience.",
        "Our engineers collectively have 25 years of relevant experience.",
        "Our leadership team has 10-20 years of industry experience.",
        "Our founders have 15+ years of professional experience.",
        "Our employees have at least 10 years of relevant experience.",
        "We have 20 years of industry experience serving customers.",
        "We bring more than 15 years of professional experience to every project.",
        "Founded by professionals with 15 years of industry experience.",
        "Candidates will meet our founders, who have 15 years of experience.",
        "Our team has over 20 years of industry experience.",
        "Our leadership team has more than 20 years of experience.",
        "Our company boasts 15 years of professional experience.",
        "Our founders collectively boast 25 years of industry experience.",
        "We have over 20 years of experience serving customers.",
    ],
)
def test_rejects_organization_history_as_applicant_experience(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.NOT_FOUND
    assert result.evidence == ()


@pytest.mark.parametrize(
    ("text", "years"),
    [
        ("Our team is looking for someone with 2 years of experience.", 2),
        ("You will join our team and bring 2 years of experience.", 2),
        (
            "Work with our engineering team and bring 3 years of professional experience.",
            3,
        ),
        ("Our company requires candidates to have 2 years of experience.", 2),
        ("Our ideal candidate has 2 years of experience.", 2),
    ],
)
def test_organization_mentions_do_not_suppress_applicant_requirements(text, years):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == years
    assert result.years_required_max == years
    assert len(result.evidence) == 1


@pytest.mark.parametrize(
    "text",
    [
        "2 years of experience",
        "2 years of experience required",
        "Requires 2 years of experience",
        "Must have 2 years of experience",
    ],
)
def test_retains_applicant_requirement_wording(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == 2
    assert result.years_required_max == 2


def test_separate_applicant_requirement_survives_organization_history():
    result = classify_experience(
        "Our team has 20 years of industry experience. "
        "Candidates need 2 years of experience."
    )

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == 2
    assert result.years_required_max == 2
    assert len(result.evidence) == 1


def test_applicant_requirement_survives_over_years_organization_history():
    result = classify_experience(
        "Our team has over 20 years of industry experience. "
        "Candidates need 2 years of experience."
    )

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == 2
    assert result.years_required_max == 2
    assert len(result.evidence) == 1


@pytest.mark.parametrize(
    "text",
    [
        "You will gain 2 years of experience in this program.",
        "This internship provides 2 years of professional experience.",
        "Build 2 years of experience while working with us.",
        "The program offers 2 years of industry experience.",
        "The role gives you 2 years of relevant experience.",
    ],
)
def test_rejects_experience_supplied_by_the_role_or_program(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.NOT_FOUND
    assert result.evidence == ()


@pytest.mark.parametrize(
    "text",
    [
        "You will bring 2 years of experience to the role.",
        "Candidates must have 2 years of experience.",
    ],
)
def test_retains_experience_brought_by_the_applicant(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.REQUIRED
    assert result.years_required_min == 2
    assert result.years_required_max == 2


@pytest.mark.parametrize(
    "text",
    [
        "experience with Python",
        "experience using Django",
        "five years since graduation",
        "a four-year degree",
        "available for a 12-month contract",
        "support a team of 10",
        "the company has operated for 5+ years",
        "A 3 years' warranty is included",
        "Revenue grew by 1.5 percent",
        "The role is split 1/2 between two teams",
        "version2 years of experience",
        "ref/2 years of experience",
        "The conference hosted 1,000 attendees",
        "Use a 1,5 ratio for the mixture",
        "The schedule is split 1/2-1 across phases",
        "Revenue ranged from 1.5-2.5 million dollars",
    ],
)
def test_ignores_non_professional_experience_numbers(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.NOT_FOUND
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert result.years_preferred is None
    assert result.evidence == ()


@pytest.mark.parametrize("text", ["", "   \n\t  "])
def test_blank_input_returns_complete_not_found_result(text):
    result = classify_experience(text)

    assert result.requirement_type is ExperienceRequirementType.NOT_FOUND
    assert result.years_required_min is None
    assert result.years_required_max is None
    assert result.years_preferred is None
    assert result.evidence == ()


def test_matching_is_case_insensitive_and_tolerates_whitespace():
    result = classify_experience("AT LEAST\n  2 YEARS OF PROFESSIONAL\tEXPERIENCE")

    assert result.years_required_min == 2
    assert result.years_required_max is None
    assert result.evidence[0].excerpt == "AT LEAST 2 YEARS OF PROFESSIONAL EXPERIENCE"


def test_evidence_uses_stable_fields_and_short_matched_context():
    description = (
        "Introduction. " + ("Background details. " * 30) + "2 years preferred."
    )

    result = classify_experience(description)

    assert result.evidence[0].rule_id == "EXP_PREFERRED_EXACT"
    assert result.evidence[0].source_field == "description_text"
    assert result.evidence[0].excerpt == "2 years preferred"
    assert len(result.evidence[0].excerpt) < len(description)


def test_result_and_evidence_are_immutable():
    result = classify_experience("1 year of experience")

    with pytest.raises(FrozenInstanceError):
        result.years_required_min = 2
    with pytest.raises(FrozenInstanceError):
        result.evidence[0].minimum = 2
    with pytest.raises(AttributeError):
        result.evidence.append(result.evidence[0])


def test_repeated_calls_are_deterministic():
    description = "1-2 years of experience; 3 years preferred."

    assert classify_experience(description) == classify_experience(description)
