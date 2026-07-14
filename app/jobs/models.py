from django.db import models
from django.utils import timezone


class EmployerSource(models.Model):
    company_name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50)
    api_instance = models.CharField(max_length=20)
    board_identifier = models.CharField(max_length=255)
    careers_url = models.URLField(max_length=1000)
    is_active = models.BooleanField(default=True)
    last_import_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_type", "api_instance", "board_identifier"),
                name="jobs_employer_source_identity_uniq",
            )
        ]


class Job(models.Model):
    class ContentCompleteness(models.TextChoices):
        FULL = "FULL", "Full"
        PARTIAL = "PARTIAL", "Partial"
        SNIPPET = "SNIPPET", "Snippet"
        UNKNOWN = "UNKNOWN", "Unknown"

    class ExperienceRequirementType(models.TextChoices):
        REQUIRED = "REQUIRED", "Required"
        PREFERRED = "PREFERRED", "Preferred"
        NICE_TO_HAVE = "NICE_TO_HAVE", "Nice to have"
        FLEXIBLE = "FLEXIBLE", "Flexible"
        AMBIGUOUS = "AMBIGUOUS", "Ambiguous"
        NOT_FOUND = "NOT_FOUND", "Not found"

    class RemoteCanadaEligibility(models.TextChoices):
        YES = "YES", "Yes"
        NO = "NO", "No"
        UNCLEAR = "UNCLEAR", "Unclear"

    class MatchBand(models.TextChoices):
        MATCH = "MATCH", "Match"
        POSSIBLE = "POSSIBLE", "Possible"
        STRETCH = "STRETCH", "Stretch"
        NOT_A_MATCH = "NOT_A_MATCH", "Not a match"
        UNCLEAR = "UNCLEAR", "Unclear"

    employer_source = models.ForeignKey(
        EmployerSource,
        on_delete=models.PROTECT,
        related_name="jobs",
    )
    source_type = models.CharField(max_length=50)
    source_job_id = models.CharField(max_length=255)
    source_url = models.URLField(max_length=1000)
    application_url = models.URLField(max_length=1000)

    title = models.CharField(max_length=500)
    company_name = models.CharField(max_length=255)
    location_text = models.TextField(blank=True)
    description_text = models.TextField(blank=True)
    description_html_raw = models.TextField(blank=True)
    content_completeness = models.CharField(
        max_length=10,
        choices=ContentCompleteness.choices,
        default=ContentCompleteness.UNKNOWN,
    )

    posted_at = models.DateTimeField(null=True, blank=True)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    last_changed_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    years_required_min = models.PositiveSmallIntegerField(null=True, blank=True)
    years_required_max = models.PositiveSmallIntegerField(null=True, blank=True)
    years_preferred = models.PositiveSmallIntegerField(null=True, blank=True)
    experience_requirement_type = models.CharField(
        max_length=20,
        choices=ExperienceRequirementType.choices,
        null=True,
        blank=True,
    )
    remote_canada_eligibility = models.CharField(
        max_length=10,
        choices=RemoteCanadaEligibility.choices,
        null=True,
        blank=True,
    )
    remote_countries = models.JSONField(null=True, blank=True)
    workplace_type = models.CharField(max_length=50, null=True, blank=True)
    office_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    office_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    distance_km_from_origin = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    career_track = models.CharField(max_length=100, null=True, blank=True)
    role_family = models.CharField(max_length=100, null=True, blank=True)
    match_band = models.CharField(
        max_length=20,
        choices=MatchBand.choices,
        null=True,
        blank=True,
    )
    classifier_version = models.CharField(max_length=100, null=True, blank=True)
    classification_explanation = models.TextField(null=True, blank=True)
    classification_evidence = models.JSONField(null=True, blank=True)

    raw_payload = models.JSONField(default=dict)
    raw_payload_hash = models.CharField(max_length=64, blank=True)

    first_viewed_at = models.DateTimeField(null=True, blank=True)
    saved_at = models.DateTimeField(null=True, blank=True)
    hidden_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_type", "source_job_id"),
                name="jobs_job_source_identity_uniq",
            ),
            models.CheckConstraint(
                condition=~models.Q(source_job_id=""),
                name="jobs_job_source_job_id_not_blank",
            ),
        ]
