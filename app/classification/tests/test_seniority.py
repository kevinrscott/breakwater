from dataclasses import FrozenInstanceError

import pytest

from classification import classify_seniority
from classification.types import SenioritySignalStrength


@pytest.mark.parametrize(
    "title",
    [
        "Senior Software Engineer",
        "Sr. Backend Developer",
        "Senior QA Automation Engineer",
    ],
)
def test_explicit_senior_titles_are_strong(title):
    result = classify_seniority(title, "Build and maintain product features.")

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == "SENIORITY_TITLE_SENIOR"
    assert result.evidence[0].source_field == "title"
    assert result.evidence[0].strength is SenioritySignalStrength.STRONG


@pytest.mark.parametrize(
    ("title", "rule_id"),
    [
        ("Senior C# Developer", "SENIORITY_TITLE_SENIOR"),
        ("Senior C++ Developer", "SENIORITY_TITLE_SENIOR"),
        ("Senior .NET Developer", "SENIORITY_TITLE_SENIOR"),
        ("Senior Python Developer", "SENIORITY_TITLE_SENIOR"),
        ("Senior Java Developer", "SENIORITY_TITLE_SENIOR"),
        ("Senior JavaScript Developer", "SENIORITY_TITLE_SENIOR"),
        ("Senior TypeScript Developer", "SENIORITY_TITLE_SENIOR"),
        ("Senior Software Engineer II", "SENIORITY_TITLE_SENIOR"),
        ("Staff Software Engineer II", "SENIORITY_TITLE_STAFF"),
        ("Principal Software Engineer II", "SENIORITY_TITLE_PRINCIPAL"),
    ],
)
def test_senior_title_technology_modifiers_and_role_levels_are_strong(title, rule_id):
    result = classify_seniority(title, "")

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == rule_id
    assert result.evidence[0].strength is SenioritySignalStrength.STRONG


@pytest.mark.parametrize(
    ("title", "rule_id"),
    [
        ("Staff Software Engineer", "SENIORITY_TITLE_STAFF"),
        ("Principal Developer", "SENIORITY_TITLE_PRINCIPAL"),
        ("Solutions Architect", "SENIORITY_TITLE_ARCHITECT"),
    ],
)
def test_staff_principal_and_architect_titles_are_strong(title, rule_id):
    result = classify_seniority(title, "")

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == rule_id


@pytest.mark.parametrize(
    ("title", "rule_id"),
    [
        ("QA Automation Lead", "SENIORITY_TITLE_LEAD"),
        ("Application Support Lead", "SENIORITY_TITLE_LEAD"),
        ("Technical Support Lead", "SENIORITY_TITLE_LEAD"),
        ("Implementation Lead", "SENIORITY_TITLE_LEAD"),
        ("IT Systems Lead", "SENIORITY_TITLE_LEAD"),
        ("Customer Support Lead", "SENIORITY_TITLE_LEAD"),
        ("Data Operations Lead", "SENIORITY_TITLE_LEAD"),
        ("Staff Technical Writer", "SENIORITY_TITLE_STAFF"),
        ("Principal Technical Writer", "SENIORITY_TITLE_PRINCIPAL"),
        ("Principal Data Analyst", "SENIORITY_TITLE_PRINCIPAL"),
        ("Enterprise Architect", "SENIORITY_TITLE_ARCHITECT"),
    ],
)
def test_supported_role_family_seniority_titles_are_strong(title, rule_id):
    result = classify_seniority(title, "")

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == rule_id
    assert result.evidence[0].strength is SenioritySignalStrength.STRONG


@pytest.mark.parametrize(
    "title",
    [
        "Lead Engineer",
        "Lead Software Developer",
        "Software Engineering Lead",
        "Technical Lead",
        "Tech Lead",
        "Engineering Team Lead",
        "Team Lead",
    ],
)
def test_genuine_lead_level_titles_are_strong(title):
    result = classify_seniority(title, "")

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == "SENIORITY_TITLE_LEAD"


@pytest.mark.parametrize(
    "title",
    [
        "Engineering Manager",
        "Director of Software Development",
        "Head of Engineering",
        "Head-of-Engineering",
    ],
)
def test_management_titles_are_strong(title):
    result = classify_seniority(title, "")

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == "SENIORITY_TITLE_MANAGEMENT"


@pytest.mark.parametrize(
    "title",
    [
        "Staff Writer",
        "Assistant to the Director",
        "Lead Generation Software Developer",
        "Senior Living Software Engineer",
    ],
)
def test_incidental_title_terms_are_not_seniority_signals(title):
    result = classify_seniority(title, "")

    assert result.has_strong_signal is False
    assert result.evidence == ()


@pytest.mark.parametrize(
    "description",
    [
        "You will manage a team of engineers building customer products.",
        "This role manages the engineering team.",
        "You will manage 6 direct reports.",
        "Act as people manager for a team of developers.",
        "Manage a team of 8 engineers.",
        "Join the platform team to manage a team of developers.",
    ],
)
def test_team_management_responsibilities_are_strong(description):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == "SENIORITY_RESPONSIBILITY_TEAM_MANAGEMENT"
    assert result.evidence[0].source_field == "description_text"


@pytest.mark.parametrize(
    "description",
    [
        "Manage a cross-functional team.",
        "Manage a cross-functional team of engineers.",
        "Manage an interdisciplinary team.",
        "Manage an engineering team.",
    ],
)
def test_adjectival_team_management_responsibilities_are_strong(description):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == "SENIORITY_RESPONSIBILITY_TEAM_MANAGEMENT"
    assert result.evidence[0].strength is SenioritySignalStrength.STRONG


@pytest.mark.parametrize(
    ("description", "rule_id"),
    [
        (
            "You will conduct performance reviews for the team.",
            "SENIORITY_RESPONSIBILITY_PERFORMANCE_MANAGEMENT",
        ),
        (
            "Own performance management and employee development.",
            "SENIORITY_RESPONSIBILITY_PERFORMANCE_MANAGEMENT",
        ),
        (
            "Hire engineers and onboard them into the organization.",
            "SENIORITY_RESPONSIBILITY_HIRING",
        ),
        (
            "You are responsible for the hiring process.",
            "SENIORITY_RESPONSIBILITY_HIRING",
        ),
        (
            "You will be hiring engineers.",
            "SENIORITY_RESPONSIBILITY_HIRING",
        ),
    ],
)
def test_hiring_and_performance_management_are_strong(description, rule_id):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == rule_id


@pytest.mark.parametrize(
    ("description", "rule_id"),
    [
        (
            "Set organization-wide technical strategy for the platform.",
            "SENIORITY_RESPONSIBILITY_ORG_STRATEGY",
        ),
        (
            "You will define company wide engineering strategy.",
            "SENIORITY_RESPONSIBILITY_ORG_STRATEGY",
        ),
        (
            "Work with leadership to set company-wide technical strategy.",
            "SENIORITY_RESPONSIBILITY_ORG_STRATEGY",
        ),
        (
            "Own engineering standards across the organization.",
            "SENIORITY_RESPONSIBILITY_ENGINEERING_STANDARDS",
        ),
        (
            "Establish organization-wide engineering standards.",
            "SENIORITY_RESPONSIBILITY_ENGINEERING_STANDARDS",
        ),
    ],
)
def test_organization_wide_ownership_is_strong(description, rule_id):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == rule_id


@pytest.mark.parametrize(
    "description",
    [
        "Lead a feature from design through delivery.",
        "You will lead the migration project.",
        "Lead small projects and coordinate with teammates.",
        "Take the lead on a customer integration.",
    ],
)
def test_task_level_uses_of_lead_are_not_seniority_signals(description):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is False
    assert result.evidence == ()


def test_mentoring_by_itself_is_supporting_only():
    result = classify_seniority(
        "Software Engineer",
        "Mentor junior developers and share knowledge with the team.",
    )

    assert result.has_strong_signal is False
    assert len(result.evidence) == 1
    assert result.evidence[0].rule_id == "SENIORITY_SUPPORT_MENTORING"
    assert result.evidence[0].strength is SenioritySignalStrength.SUPPORTING


@pytest.mark.parametrize(
    "description",
    [
        "Work closely with senior engineers on product features.",
        "Collaborate with company leadership on priorities.",
        "This role reports to the Engineering Manager.",
        "Learn architecture practices from a Principal Engineer.",
        "Present project updates to the Director of Engineering.",
        "Experience with performance management software is helpful.",
        "Collaborate with hiring managers and company leadership.",
        "Participate in hiring engineers with the Engineering Manager.",
        "Help define engineering standards with senior engineers.",
    ],
)
def test_incidental_references_to_senior_employees_are_not_signals(description):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is False
    assert result.evidence == ()


@pytest.mark.parametrize(
    "description",
    [
        "Interview senior engineers as part of the interview panel.",
        "Hire senior engineers for the manager's team.",
        "Own performance management software features.",
        "Own performance management functionality in our HR platform.",
        "Own performance management capabilities in our HR platform.",
        "Own performance management module development.",
        "Own performance management integration work.",
        "Own performance management solution design.",
        "Manage the team backlog.",
        "Manage the team's backlog.",
        "Manage a team project through delivery.",
        "Manage team projects and delivery schedules.",
        "Manage the team's release workflow.",
    ],
)
def test_senior_people_and_management_products_are_not_signals(description):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is False
    assert result.evidence == ()


@pytest.mark.parametrize(
    "description",
    [
        "You will work with managers who hire engineers.",
        "The CTO sets company-wide technical strategy.",
        "Our company hires engineers across Canada.",
        "The Head of Engineering will hire engineers.",
        "Our Principal Engineers own engineering standards.",
        (
            "Engineering Managers manage a team of developers; "
            "this position is an IC role."
        ),
        "Your manager will conduct performance reviews.",
    ],
)
def test_responsibilities_belonging_to_other_people_are_not_signals(description):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is False
    assert result.evidence == ()


@pytest.mark.parametrize(
    "description",
    [
        "The engineering manager is responsible for hiring engineers.",
        "Your manager is responsible for performance management.",
        "Managers are expected to hire engineers.",
        "Our CTO is responsible for setting company-wide technical strategy.",
        "The team is responsible for hiring engineers.",
        (
            "You will work with the engineering manager, who is responsible "
            "for hiring engineers."
        ),
    ],
)
def test_other_party_grammatical_bridges_do_not_create_signals(description):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is False
    assert result.evidence == ()


@pytest.mark.parametrize(
    "description",
    [
        "Build software that allows managers to manage a team of developers.",
        "Work with the payments team lead who hires engineers.",
        "The Director of Engineering will hire engineers.",
        "The other team's manager will hire engineers.",
    ],
)
def test_other_party_role_variations_do_not_create_signals(description):
    result = classify_seniority("Software Engineer", description)

    assert result.has_strong_signal is False
    assert result.evidence == ()


def test_other_party_reference_on_prior_line_does_not_suppress_candidate_bullet():
    result = classify_seniority(
        "Software Engineer",
        "Reports to the Engineering Manager\nHire engineers.",
    )

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == "SENIORITY_RESPONSIBILITY_HIRING"


@pytest.mark.parametrize(
    ("title", "description", "rule_id"),
    [
        ("sTaFf / Software Engineer", "", "SENIORITY_TITLE_STAFF"),
        ("SR. SOFTWARE ENGINEER", "", "SENIORITY_TITLE_SENIOR"),
        ("Lead - Software Engineer", "", "SENIORITY_TITLE_LEAD"),
        (
            "Software Engineer",
            "Own PERFORMANCE-MANAGEMENT for the team.",
            "SENIORITY_RESPONSIBILITY_PERFORMANCE_MANAGEMENT",
        ),
        (
            "Software Engineer",
            "Define organization-wide technical strategy.",
            "SENIORITY_RESPONSIBILITY_ORG_STRATEGY",
        ),
    ],
)
def test_matching_handles_casing_and_punctuation(title, description, rule_id):
    result = classify_seniority(title, description)

    assert result.has_strong_signal is True
    assert result.evidence[0].rule_id == rule_id


def test_multiple_signals_are_all_preserved_in_deterministic_order():
    title = "Senior Engineering Manager"
    description = (
        "Manage a team of developers. Hire engineers. "
        "Own engineering standards. Mentor junior developers."
    )

    result = classify_seniority(title, description)

    assert result.has_strong_signal is True
    assert [item.rule_id for item in result.evidence] == [
        "SENIORITY_TITLE_SENIOR",
        "SENIORITY_TITLE_MANAGEMENT",
        "SENIORITY_RESPONSIBILITY_TEAM_MANAGEMENT",
        "SENIORITY_RESPONSIBILITY_HIRING",
        "SENIORITY_RESPONSIBILITY_ENGINEERING_STANDARDS",
        "SENIORITY_SUPPORT_MENTORING",
    ]


def test_evidence_contains_only_the_short_relevant_excerpt():
    description = (
        "General background. " + ("More unrelated details. " * 30) + "Hire engineers."
    )

    result = classify_seniority("Software Engineer", description)

    assert result.evidence[0].source_field == "description_text"
    assert result.evidence[0].excerpt == "Hire engineers"
    assert len(result.evidence[0].excerpt) < len(description)


def test_blank_inputs_return_a_complete_non_strong_result():
    result = classify_seniority("  ", "\n\t")

    assert result.has_strong_signal is False
    assert result.evidence == ()


def test_result_and_evidence_are_immutable():
    result = classify_seniority("Senior Software Engineer", "")

    with pytest.raises(FrozenInstanceError):
        result.has_strong_signal = False
    with pytest.raises(FrozenInstanceError):
        result.evidence[0].rule_id = "CHANGED"
    with pytest.raises(AttributeError):
        result.evidence.append(result.evidence[0])


def test_repeated_calls_are_deterministic():
    title = "Lead Software Engineer"
    description = "Manage a team and mentor junior developers."

    assert classify_seniority(title, description) == classify_seniority(
        title, description
    )
