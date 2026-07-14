from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from jobs.models import EmployerSource, Job


class JobModelTests(TestCase):
    def setUp(self):
        self.employer_source = EmployerSource.objects.create(
            company_name="Example Employer",
            source_type="LEVER",
            api_instance="global",
            board_identifier="example-employer",
            careers_url="https://jobs.example.com/",
        )

    def create_job(self, **overrides):
        values = {
            "employer_source": self.employer_source,
            "source_type": "LEVER",
            "source_job_id": "posting-1",
            "source_url": "https://jobs.example.com/posting-1",
            "application_url": "https://jobs.example.com/posting-1/apply",
            "title": "Software Developer",
            "company_name": "Example Employer",
        }
        values.update(overrides)
        return Job.objects.create(**values)

    def test_employer_source_identity_is_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            EmployerSource.objects.create(
                company_name="Renamed Employer",
                source_type="LEVER",
                api_instance="global",
                board_identifier="example-employer",
                careers_url="https://careers.example.com/",
            )

    def test_job_source_identity_is_unique(self):
        self.create_job()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_job(title="Updated title")

    def test_source_job_id_cannot_be_blank(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_job(source_job_id="")

    def test_employer_source_is_protected(self):
        self.create_job()

        with self.assertRaises(ProtectedError):
            self.employer_source.delete()

    def test_review_timestamps_are_independent(self):
        saved_at = timezone.now()

        job = self.create_job(saved_at=saved_at)

        self.assertEqual(job.saved_at, saved_at)
        self.assertIsNone(job.first_viewed_at)
        self.assertIsNone(job.hidden_at)
        self.assertIsNone(job.applied_at)

    def test_classification_fields_are_nullable(self):
        job = self.create_job()

        nullable_fields = (
            "years_required_min",
            "years_required_max",
            "years_preferred",
            "experience_requirement_type",
            "remote_canada_eligibility",
            "remote_countries",
            "workplace_type",
            "office_latitude",
            "office_longitude",
            "distance_km_from_origin",
            "career_track",
            "role_family",
            "match_band",
            "classifier_version",
            "classification_explanation",
            "classification_evidence",
        )
        for field_name in nullable_fields:
            with self.subTest(field_name=field_name):
                self.assertIsNone(getattr(job, field_name))
