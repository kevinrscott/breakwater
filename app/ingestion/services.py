import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from ingestion.types import NormalizedJobInput
from jobs.models import EmployerSource, Job


class JobProvenanceMismatchError(ValueError):
    """Raised when a source identity is already owned by another employer source."""


@dataclass(frozen=True, slots=True)
class JobUpsertResult:
    job: Job
    created: bool
    changed: bool
    reactivated: bool

    @property
    def unchanged(self) -> bool:
        return not (self.created or self.changed or self.reactivated)


def upsert_normalized_job(
    *,
    employer_source: EmployerSource,
    normalized_job: NormalizedJobInput,
    imported_at: datetime | None = None,
) -> JobUpsertResult:
    """Create or update one normalized job without touching derived or review state."""
    import_timestamp = imported_at if imported_at is not None else timezone.now()
    raw_payload = dict(normalized_job.raw_payload)
    payload_hash = _source_content_hash(
        source_type=employer_source.source_type,
        normalized_job=normalized_job,
        raw_payload=raw_payload,
    )

    create_values = {
        "employer_source": employer_source,
        "source_url": normalized_job.source_url,
        "application_url": normalized_job.application_url,
        "title": normalized_job.title,
        "company_name": normalized_job.company_name,
        "location_text": normalized_job.location_text,
        "description_text": normalized_job.description_text,
        "first_seen_at": import_timestamp,
        "last_seen_at": import_timestamp,
        "last_changed_at": import_timestamp,
        "is_active": True,
        "raw_payload": raw_payload,
        "raw_payload_hash": payload_hash,
    }

    with transaction.atomic():
        job, created = Job.objects.select_for_update().get_or_create(
            source_type=employer_source.source_type,
            source_job_id=normalized_job.source_job_id,
            defaults=create_values,
        )
        if created:
            return JobUpsertResult(
                job=job,
                created=True,
                changed=False,
                reactivated=False,
            )

        if job.employer_source_id != employer_source.pk:
            raise JobProvenanceMismatchError(
                "Job source identity "
                f"({employer_source.source_type!r}, "
                f"{normalized_job.source_job_id!r}) is already associated with "
                f"employer source {job.employer_source.board_identifier!r}, not "
                f"{employer_source.board_identifier!r}."
            )

        changed = job.raw_payload_hash != payload_hash
        reactivated = not job.is_active
        update_fields = ["last_seen_at", "updated_at"]
        job.last_seen_at = import_timestamp

        if changed:
            job.source_url = normalized_job.source_url
            job.application_url = normalized_job.application_url
            job.title = normalized_job.title
            job.company_name = normalized_job.company_name
            job.location_text = normalized_job.location_text
            job.description_text = normalized_job.description_text
            job.raw_payload = raw_payload
            job.raw_payload_hash = payload_hash
            job.last_changed_at = import_timestamp
            update_fields.extend(
                [
                    "source_url",
                    "application_url",
                    "title",
                    "company_name",
                    "location_text",
                    "description_text",
                    "raw_payload",
                    "raw_payload_hash",
                    "last_changed_at",
                ]
            )

        if reactivated:
            job.is_active = True
            update_fields.append("is_active")

        job.save(update_fields=update_fields)

    return JobUpsertResult(
        job=job,
        created=False,
        changed=changed,
        reactivated=reactivated,
    )


def _source_content_hash(
    *,
    source_type: str,
    normalized_job: NormalizedJobInput,
    raw_payload: dict[str, object],
) -> str:
    source_content = {
        "source_type": source_type,
        "source_job_id": normalized_job.source_job_id,
        "source_url": normalized_job.source_url,
        "application_url": normalized_job.application_url,
        "title": normalized_job.title,
        "company_name": normalized_job.company_name,
        "location_text": normalized_job.location_text,
        "description_text": normalized_job.description_text,
        "country_evidence": normalized_job.country_evidence,
        "workplace_evidence": normalized_job.workplace_evidence,
        "raw_payload": raw_payload,
    }
    canonical_content = json.dumps(
        source_content,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()
