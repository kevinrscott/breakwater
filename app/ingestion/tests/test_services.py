from datetime import UTC, datetime
from decimal import Decimal

from django.test import TestCase

from ingestion.services import (
    JobProvenanceMismatchError,
    upsert_normalized_job,
)
from ingestion.types import NormalizedJobInput
from jobs.models import EmployerSource, Job


class UpsertNormalizedJobTests(TestCase):
    def setUp(self):
        self.employer_source = EmployerSource.objects.create(
            company_name="Example Employer",
            source_type="LEVER",
            api_instance="global",
            board_identifier="example-employer",
            careers_url="https://jobs.example.com/",
        )

    def normalized_job(self, **overrides) -> NormalizedJobInput:
        values = {
            "source_job_id": "posting-1",
            "title": "Software Developer",
            "company_name": "Example Employer",
            "source_url": "https://jobs.example.com/posting-1",
            "application_url": "https://jobs.example.com/posting-1/apply",
            "location_text": "Canada; Toronto, Ontario",
            "country_evidence": "CA",
            "workplace_evidence": "remote",
            "description_text": "Build reliable services.",
            "raw_payload": {
                "id": "posting-1",
                "details": {"country": "CA", "workplace": "remote"},
            },
        }
        values.update(overrides)
        return NormalizedJobInput(**values)

    def test_creates_job_with_source_fields_and_import_timestamps(self):
        imported_at = datetime(2026, 7, 15, 16, 30, tzinfo=UTC)
        normalized_job = self.normalized_job()

        result = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=normalized_job,
            imported_at=imported_at,
        )

        self.assertTrue(result.created)
        self.assertFalse(result.changed)
        self.assertFalse(result.reactivated)
        self.assertFalse(result.unchanged)
        self.assertEqual(Job.objects.count(), 1)

        job = result.job
        self.assertEqual(job.employer_source, self.employer_source)
        self.assertEqual(job.source_type, "LEVER")
        self.assertEqual(job.source_job_id, normalized_job.source_job_id)
        self.assertEqual(job.source_url, normalized_job.source_url)
        self.assertEqual(job.application_url, normalized_job.application_url)
        self.assertEqual(job.title, normalized_job.title)
        self.assertEqual(job.company_name, normalized_job.company_name)
        self.assertEqual(job.location_text, normalized_job.location_text)
        self.assertEqual(job.description_text, normalized_job.description_text)
        self.assertEqual(job.raw_payload, normalized_job.raw_payload)
        self.assertEqual(len(job.raw_payload_hash), 64)
        self.assertEqual(job.first_seen_at, imported_at)
        self.assertEqual(job.last_seen_at, imported_at)
        self.assertEqual(job.last_changed_at, imported_at)
        self.assertTrue(job.is_active)
        self.assertEqual(job.description_html_raw, "")
        self.assertEqual(job.content_completeness, Job.ContentCompleteness.UNKNOWN)
        self.assertIsNone(job.posted_at)
        self.assertIsNone(job.remote_canada_eligibility)
        self.assertIsNone(job.remote_countries)
        self.assertIsNone(job.workplace_type)

    def test_equivalent_payload_key_order_is_unchanged(self):
        first_import = datetime(2026, 7, 15, 16, 30, tzinfo=UTC)
        second_import = datetime(2026, 7, 15, 17, 30, tzinfo=UTC)
        first_input = self.normalized_job(
            raw_payload={
                "id": "posting-1",
                "details": {"country": "CA", "workplace": "remote"},
            }
        )
        first_result = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=first_input,
            imported_at=first_import,
        )
        first_hash = first_result.job.raw_payload_hash
        first_viewed_at = datetime(2026, 7, 15, 16, 40, tzinfo=UTC)
        saved_at = datetime(2026, 7, 15, 16, 45, tzinfo=UTC)
        hidden_at = datetime(2026, 7, 15, 16, 50, tzinfo=UTC)
        applied_at = datetime(2026, 7, 15, 16, 55, tzinfo=UTC)
        first_result.job.first_viewed_at = first_viewed_at
        first_result.job.saved_at = saved_at
        first_result.job.hidden_at = hidden_at
        first_result.job.applied_at = applied_at
        first_result.job.notes = "Owner note"
        first_result.job.save()
        second_input = self.normalized_job(
            raw_payload={
                "details": {"workplace": "remote", "country": "CA"},
                "id": "posting-1",
            }
        )

        result = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=second_input,
            imported_at=second_import,
        )

        self.assertFalse(result.created)
        self.assertFalse(result.changed)
        self.assertFalse(result.reactivated)
        self.assertTrue(result.unchanged)
        self.assertEqual(Job.objects.count(), 1)
        result.job.refresh_from_db()
        self.assertEqual(result.job.raw_payload_hash, first_hash)
        self.assertEqual(result.job.first_seen_at, first_import)
        self.assertEqual(result.job.last_seen_at, second_import)
        self.assertEqual(result.job.last_changed_at, first_import)
        self.assertEqual(result.job.first_viewed_at, first_viewed_at)
        self.assertEqual(result.job.saved_at, saved_at)
        self.assertEqual(result.job.hidden_at, hidden_at)
        self.assertEqual(result.job.applied_at, applied_at)
        self.assertEqual(result.job.notes, "Owner note")

    def test_normalized_field_change_updates_job_when_raw_payload_is_unchanged(self):
        first_import = datetime(2026, 7, 15, 16, 30, tzinfo=UTC)
        second_import = datetime(2026, 7, 15, 17, 30, tzinfo=UTC)
        raw_payload = {
            "id": "posting-1",
            "details": {"country": "CA", "workplace": "remote"},
        }
        first_result = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=self.normalized_job(raw_payload=raw_payload),
            imported_at=first_import,
        )
        first_hash = first_result.job.raw_payload_hash

        result = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=self.normalized_job(
                title="Senior Software Developer",
                raw_payload=raw_payload,
            ),
            imported_at=second_import,
        )

        self.assertFalse(result.created)
        self.assertTrue(result.changed)
        result.job.refresh_from_db()
        self.assertNotEqual(result.job.raw_payload_hash, first_hash)
        self.assertEqual(result.job.title, "Senior Software Developer")
        self.assertEqual(result.job.last_changed_at, second_import)
        self.assertEqual(Job.objects.count(), 1)

    def test_changed_reimport_updates_source_content_and_preserves_other_state(self):
        first_import = datetime(2026, 7, 15, 16, 30, tzinfo=UTC)
        second_import = datetime(2026, 7, 15, 17, 30, tzinfo=UTC)
        first_viewed_at = datetime(2026, 7, 15, 16, 40, tzinfo=UTC)
        saved_at = datetime(2026, 7, 15, 16, 45, tzinfo=UTC)
        hidden_at = datetime(2026, 7, 15, 16, 50, tzinfo=UTC)
        applied_at = datetime(2026, 7, 15, 16, 55, tzinfo=UTC)
        initial = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=self.normalized_job(),
            imported_at=first_import,
        ).job
        initial.first_viewed_at = first_viewed_at
        initial.saved_at = saved_at
        initial.hidden_at = hidden_at
        initial.applied_at = applied_at
        initial.notes = "Owner note"
        initial.years_required_min = 1
        initial.years_required_max = 2
        initial.years_preferred = 2
        initial.experience_requirement_type = Job.ExperienceRequirementType.REQUIRED
        initial.remote_canada_eligibility = Job.RemoteCanadaEligibility.YES
        initial.remote_countries = ["CA"]
        initial.workplace_type = "REMOTE"
        initial.office_latitude = Decimal("49.165900")
        initial.office_longitude = Decimal("-123.940100")
        initial.distance_km_from_origin = Decimal("12.34")
        initial.career_track = "SOFTWARE"
        initial.role_family = "BACKEND"
        initial.match_band = Job.MatchBand.POSSIBLE
        initial.classifier_version = "test-v1"
        initial.classification_explanation = "Test explanation"
        initial.classification_evidence = {"experience": [{"minimum": 1}]}
        initial.is_active = False
        initial.save()
        first_hash = initial.raw_payload_hash
        changed_input = self.normalized_job(
            title="Senior Software Developer",
            company_name="Updated Employer Name",
            source_url="https://jobs.example.com/posting-1-updated",
            application_url="https://jobs.example.com/posting-1-updated/apply",
            location_text="Vancouver, BC",
            description_text="Lead reliable services.",
            raw_payload={"id": "posting-1", "revision": 2},
        )

        result = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=changed_input,
            imported_at=second_import,
        )

        self.assertFalse(result.created)
        self.assertTrue(result.changed)
        self.assertTrue(result.reactivated)
        self.assertFalse(result.unchanged)
        result.job.refresh_from_db()
        job = result.job
        self.assertEqual(job.title, changed_input.title)
        self.assertEqual(job.company_name, changed_input.company_name)
        self.assertEqual(job.source_url, changed_input.source_url)
        self.assertEqual(job.application_url, changed_input.application_url)
        self.assertEqual(job.location_text, changed_input.location_text)
        self.assertEqual(job.description_text, changed_input.description_text)
        self.assertEqual(job.raw_payload, changed_input.raw_payload)
        self.assertNotEqual(job.raw_payload_hash, first_hash)
        self.assertEqual(job.first_seen_at, first_import)
        self.assertEqual(job.last_seen_at, second_import)
        self.assertEqual(job.last_changed_at, second_import)
        self.assertTrue(job.is_active)
        self.assertEqual(job.first_viewed_at, first_viewed_at)
        self.assertEqual(job.saved_at, saved_at)
        self.assertEqual(job.hidden_at, hidden_at)
        self.assertEqual(job.applied_at, applied_at)
        self.assertEqual(job.notes, "Owner note")
        self.assertEqual(job.years_required_min, 1)
        self.assertEqual(job.years_required_max, 2)
        self.assertEqual(job.years_preferred, 2)
        self.assertEqual(
            job.experience_requirement_type,
            Job.ExperienceRequirementType.REQUIRED,
        )
        self.assertEqual(
            job.remote_canada_eligibility,
            Job.RemoteCanadaEligibility.YES,
        )
        self.assertEqual(job.remote_countries, ["CA"])
        self.assertEqual(job.workplace_type, "REMOTE")
        self.assertEqual(job.office_latitude, Decimal("49.165900"))
        self.assertEqual(job.office_longitude, Decimal("-123.940100"))
        self.assertEqual(job.distance_km_from_origin, Decimal("12.34"))
        self.assertEqual(job.career_track, "SOFTWARE")
        self.assertEqual(job.role_family, "BACKEND")
        self.assertEqual(job.match_band, Job.MatchBand.POSSIBLE)
        self.assertEqual(job.classifier_version, "test-v1")
        self.assertEqual(job.classification_explanation, "Test explanation")
        self.assertEqual(
            job.classification_evidence,
            {"experience": [{"minimum": 1}]},
        )

    def test_unchanged_inactive_job_is_reactivated_without_changing_content(self):
        first_import = datetime(2026, 7, 15, 16, 30, tzinfo=UTC)
        second_import = datetime(2026, 7, 15, 17, 30, tzinfo=UTC)
        job = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=self.normalized_job(),
            imported_at=first_import,
        ).job
        job.is_active = False
        job.save(update_fields=["is_active"])

        result = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=self.normalized_job(),
            imported_at=second_import,
        )

        self.assertFalse(result.created)
        self.assertFalse(result.changed)
        self.assertTrue(result.reactivated)
        self.assertFalse(result.unchanged)
        result.job.refresh_from_db()
        self.assertTrue(result.job.is_active)
        self.assertEqual(result.job.last_seen_at, second_import)
        self.assertEqual(result.job.last_changed_at, first_import)

    def test_normalized_evidence_changes_hash_without_mapping_classification(self):
        first_import = datetime(2026, 7, 15, 16, 30, tzinfo=UTC)
        second_import = datetime(2026, 7, 15, 17, 30, tzinfo=UTC)
        job = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=self.normalized_job(),
            imported_at=first_import,
        ).job
        first_hash = job.raw_payload_hash

        result = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=self.normalized_job(
                country_evidence="US",
                workplace_evidence="hybrid",
            ),
            imported_at=second_import,
        )

        self.assertTrue(result.changed)
        result.job.refresh_from_db()
        self.assertNotEqual(result.job.raw_payload_hash, first_hash)
        self.assertIsNone(result.job.remote_canada_eligibility)
        self.assertIsNone(result.job.remote_countries)
        self.assertIsNone(result.job.workplace_type)

    def test_existing_identity_with_different_employer_source_fails(self):
        imported_at = datetime(2026, 7, 15, 16, 30, tzinfo=UTC)
        existing_job = upsert_normalized_job(
            employer_source=self.employer_source,
            normalized_job=self.normalized_job(),
            imported_at=imported_at,
        ).job
        other_source = EmployerSource.objects.create(
            company_name="Other Employer",
            source_type="LEVER",
            api_instance="global",
            board_identifier="other-employer",
            careers_url="https://jobs.example.org/",
        )

        with self.assertRaisesMessage(
            JobProvenanceMismatchError,
            "is already associated with employer source 'example-employer', "
            "not 'other-employer'",
        ):
            upsert_normalized_job(
                employer_source=other_source,
                normalized_job=self.normalized_job(),
                imported_at=datetime(2026, 7, 15, 17, 30, tzinfo=UTC),
            )

        self.assertEqual(Job.objects.count(), 1)
        existing_job.refresh_from_db()
        self.assertEqual(existing_job.employer_source, self.employer_source)
        self.assertEqual(existing_job.last_seen_at, imported_at)
