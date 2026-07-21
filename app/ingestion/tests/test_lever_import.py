import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError

from django.test import TestCase

from ingestion.adapters.lever import normalize_lever_posting
from ingestion.adapters.lever_fetch import LeverFetchError
from ingestion.normalization import NormalizationError
from ingestion.services import (
    JobProvenanceMismatchError,
    LeverImportResult,
    import_lever_source,
    upsert_normalized_job,
)
from jobs.models import EmployerSource, Job


class _FakeResponse:
    def __init__(self, postings: list[dict[str, object]]) -> None:
        self.body = json.dumps(postings).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self) -> bytes:
        return self.body


def _http_error(status_code: int) -> HTTPError:
    return HTTPError(
        "https://api.lever.co/v0/postings/example?mode=json",
        status_code,
        "Test response",
        Message(),
        None,
    )


def _posting(
    posting_id: str,
    *,
    title: str | None = None,
    description: str = "Build reliable services.",
) -> dict[str, object]:
    return {
        "id": posting_id,
        "text": title or f"Software Developer {posting_id}",
        "hostedUrl": f"https://jobs.example.com/{posting_id}",
        "applyUrl": f"https://jobs.example.com/{posting_id}/apply",
        "descriptionPlain": description,
        "categories": {"allLocations": ["Canada", "Toronto, Ontario"]},
        "country": "CA",
        "workplaceType": "remote",
    }


class ImportLeverSourceTests(TestCase):
    def create_source(self, **overrides) -> EmployerSource:
        values = {
            "company_name": "Example Employer",
            "source_type": "LEVER",
            "api_instance": "global",
            "board_identifier": "example-employer",
            "careers_url": "https://jobs.example.com/",
        }
        values.update(overrides)
        return EmployerSource.objects.create(**values)

    def persist_posting(
        self,
        source: EmployerSource,
        posting: dict[str, object],
        imported_at: datetime,
    ) -> Job:
        normalized_job = normalize_lever_posting(
            posting,
            company_name=source.company_name,
        )
        return upsert_normalized_job(
            employer_source=source,
            normalized_job=normalized_job,
            imported_at=imported_at,
        ).job

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_imports_new_postings_with_source_configuration_and_one_timestamp(
        self,
        mock_urlopen,
    ):
        attempted_at = datetime(2026, 7, 19, 16, 30, tzinfo=UTC)
        source = self.create_source(
            company_name="  Configured Employer  ",
            api_instance="eu",
            board_identifier="configured/board",
            consecutive_failures=3,
        )
        postings = [_posting("posting-1"), _posting("posting-2")]
        mock_urlopen.return_value = _FakeResponse(postings)

        with patch("ingestion.services.timezone.now", return_value=attempted_at):
            result = import_lever_source(source)

        self.assertEqual(
            result,
            LeverImportResult(
                fetched=2,
                created=2,
                changed=0,
                unchanged=0,
                reactivated=0,
            ),
        )
        with self.assertRaises(FrozenInstanceError):
            result.fetched = 3

        request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://api.eu.lever.co/v0/postings/"
            "configured%2Fboard?mode=json",
        )
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 10.0)

        source.refresh_from_db()
        self.assertEqual(source.last_import_at, attempted_at)
        self.assertEqual(source.last_success_at, attempted_at)
        self.assertEqual(source.consecutive_failures, 0)

        jobs = list(Job.objects.order_by("source_job_id"))
        self.assertEqual(len(jobs), 2)
        for job in jobs:
            self.assertEqual(job.company_name, "Configured Employer")
            self.assertEqual(job.first_seen_at, attempted_at)
            self.assertEqual(job.last_seen_at, attempted_at)
            self.assertEqual(job.last_changed_at, attempted_at)

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_counts_changed_unchanged_and_reactivated_independently(
        self,
        mock_urlopen,
    ):
        first_import = datetime(2026, 7, 18, 16, 30, tzinfo=UTC)
        attempted_at = datetime(2026, 7, 19, 16, 30, tzinfo=UTC)
        source = self.create_source()
        initial_postings = {
            posting_id: _posting(posting_id)
            for posting_id in (
                "changed",
                "unchanged",
                "changed-reactivated",
                "unchanged-reactivated",
            )
        }
        jobs = {
            posting_id: self.persist_posting(source, posting, first_import)
            for posting_id, posting in initial_postings.items()
        }
        Job.objects.filter(
            pk__in=[
                jobs["changed-reactivated"].pk,
                jobs["unchanged-reactivated"].pk,
            ]
        ).update(is_active=False)
        fetched_postings = [
            _posting("new"),
            _posting("changed", title="Changed title"),
            initial_postings["unchanged"],
            _posting("changed-reactivated", title="Changed and reactivated"),
            initial_postings["unchanged-reactivated"],
        ]
        mock_urlopen.return_value = _FakeResponse(fetched_postings)

        with patch("ingestion.services.timezone.now", return_value=attempted_at):
            result = import_lever_source(source)

        self.assertEqual(
            result,
            LeverImportResult(
                fetched=5,
                created=1,
                changed=2,
                unchanged=1,
                reactivated=2,
            ),
        )
        changed_reactivated = Job.objects.get(
            source_job_id="changed-reactivated"
        )
        self.assertTrue(changed_reactivated.is_active)
        self.assertEqual(changed_reactivated.last_changed_at, attempted_at)
        unchanged_reactivated = Job.objects.get(
            source_job_id="unchanged-reactivated"
        )
        self.assertTrue(unchanged_reactivated.is_active)
        self.assertEqual(unchanged_reactivated.last_changed_at, first_import)
        self.assertEqual(unchanged_reactivated.last_seen_at, attempted_at)

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_rejects_non_lever_source_before_http_and_records_failure(
        self,
        mock_urlopen,
    ):
        previous_success = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
        attempted_at = datetime(2026, 7, 19, 16, 30, tzinfo=UTC)
        source = self.create_source(
            source_type="GREENHOUSE",
            last_success_at=previous_success,
            consecutive_failures=2,
        )

        with patch("ingestion.services.timezone.now", return_value=attempted_at):
            with self.assertRaisesMessage(
                ValueError,
                "source_type 'LEVER'",
            ):
                import_lever_source(source)

        mock_urlopen.assert_not_called()
        self.assertEqual(Job.objects.count(), 0)
        source.refresh_from_db()
        self.assertEqual(source.last_import_at, attempted_at)
        self.assertEqual(source.last_success_at, previous_success)
        self.assertEqual(source.consecutive_failures, 3)

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_fetch_failure_records_health_and_propagates_fetch_error(
        self,
        mock_urlopen,
    ):
        previous_success = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
        attempted_at = datetime(2026, 7, 19, 16, 30, tzinfo=UTC)
        source = self.create_source(
            last_success_at=previous_success,
            consecutive_failures=1,
        )
        mock_urlopen.side_effect = _http_error(404)

        with patch("ingestion.services.timezone.now", return_value=attempted_at):
            with self.assertRaises(LeverFetchError) as context:
                import_lever_source(source)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.attempts, 1)
        self.assertEqual(Job.objects.count(), 0)
        source.refresh_from_db()
        self.assertEqual(source.last_import_at, attempted_at)
        self.assertEqual(source.last_success_at, previous_success)
        self.assertEqual(source.consecutive_failures, 2)

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_normalization_failure_prevents_all_job_persistence(
        self,
        mock_urlopen,
    ):
        previous_success = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
        attempted_at = datetime(2026, 7, 19, 16, 30, tzinfo=UTC)
        source = self.create_source(last_success_at=previous_success)
        malformed_posting = _posting("malformed")
        del malformed_posting["text"]
        mock_urlopen.return_value = _FakeResponse(
            [_posting("valid-first"), malformed_posting]
        )

        with patch("ingestion.services.timezone.now", return_value=attempted_at):
            with self.assertRaisesMessage(
                NormalizationError,
                "Lever field 'text' must be a nonblank string.",
            ):
                import_lever_source(source)

        self.assertEqual(Job.objects.count(), 0)
        source.refresh_from_db()
        self.assertEqual(source.last_import_at, attempted_at)
        self.assertEqual(source.last_success_at, previous_success)
        self.assertEqual(source.consecutive_failures, 1)

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_later_provenance_conflict_rolls_back_jobs_then_records_failure(
        self,
        mock_urlopen,
    ):
        first_import = datetime(2026, 7, 18, 10, 0, tzinfo=UTC)
        previous_success = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
        attempted_at = datetime(2026, 7, 19, 16, 30, tzinfo=UTC)
        source = self.create_source(
            last_success_at=previous_success,
            consecutive_failures=2,
        )
        other_source = self.create_source(
            company_name="Other Employer",
            board_identifier="other-employer",
            careers_url="https://jobs.other.example.com/",
        )
        conflicting_posting = _posting("conflict")
        existing_job = self.persist_posting(
            other_source,
            conflicting_posting,
            first_import,
        )
        mock_urlopen.return_value = _FakeResponse(
            [_posting("inserted-before-conflict"), conflicting_posting]
        )

        with patch("ingestion.services.timezone.now", return_value=attempted_at):
            with self.assertRaises(JobProvenanceMismatchError) as context:
                import_lever_source(source)

        self.assertIn("other-employer", str(context.exception))
        self.assertFalse(
            Job.objects.filter(source_job_id="inserted-before-conflict").exists()
        )
        self.assertEqual(Job.objects.count(), 1)
        existing_job.refresh_from_db()
        self.assertEqual(existing_job.employer_source, other_source)
        self.assertEqual(existing_job.last_seen_at, first_import)

        source.refresh_from_db()
        self.assertEqual(source.last_import_at, attempted_at)
        self.assertEqual(source.last_success_at, previous_success)
        self.assertEqual(source.consecutive_failures, 3)
