import math

from django.test import SimpleTestCase

from ingestion.adapters.lever import normalize_lever_posting
from ingestion.normalization import NormalizationError
from ingestion.types import JSONValue, NormalizedJobInput


class NormalizeLeverPostingTests(SimpleTestCase):
    def representative_payload(self) -> dict[str, JSONValue]:
        return {
            "id": " posting-123 ",
            "text": " Software Developer ",
            "hostedUrl": "https://jobs.lever.co/example/posting-123",
            "applyUrl": "https://jobs.lever.co/example/posting-123/apply",
            "categories": {
                "location": "Remote - Canada",
                "allLocations": ["Canada", "Toronto, Ontario", "Canada"],
            },
            "country": "CA",
            "workplaceType": "remote",
            "descriptionPlain": (
                " Build reliable services.\r\n\r\n Work with the team. "
            ),
            "lists": [
                {
                    "text": "Responsibilities",
                    "content": (
                        "<ul><li>Write <strong>Python</strong></li>"
                        "<li>Ship safely &amp; often<br>together</li></ul>"
                    ),
                }
            ],
            "additionalPlain": " Equal opportunity employer. ",
        }

    def test_normalizes_representative_posting(self):
        raw_payload = self.representative_payload()

        normalized = normalize_lever_posting(
            raw_payload,
            company_name=" Example Company ",
        )

        self.assertIsInstance(normalized, NormalizedJobInput)
        self.assertEqual(normalized.source_job_id, "posting-123")
        self.assertEqual(normalized.title, "Software Developer")
        self.assertEqual(normalized.company_name, "Example Company")
        self.assertEqual(
            normalized.source_url,
            "https://jobs.lever.co/example/posting-123",
        )
        self.assertEqual(
            normalized.application_url,
            "https://jobs.lever.co/example/posting-123/apply",
        )
        self.assertEqual(normalized.location_text, "Canada; Toronto, Ontario")
        self.assertEqual(normalized.country_evidence, "CA")
        self.assertEqual(normalized.workplace_evidence, "remote")
        self.assertEqual(
            normalized.description_text,
            "Build reliable services.\n\n"
            "Work with the team.\n\n"
            "Write Python\n\n"
            "Ship safely & often\n"
            "together\n\n"
            "Equal opportunity employer.",
        )
        self.assertEqual(normalized.raw_payload, raw_payload)
        self.assertIsNot(normalized.raw_payload, raw_payload)

    def test_uses_primary_location_and_allows_missing_optional_evidence(self):
        payload = self.representative_payload()
        payload["categories"] = {"location": "  Vancouver, BC  "}
        payload["country"] = None
        payload["workplaceType"] = None
        payload["descriptionPlain"] = None
        payload["lists"] = []
        payload["additionalPlain"] = None

        normalized = normalize_lever_posting(
            payload,
            company_name="Example Company",
        )

        self.assertEqual(normalized.location_text, "Vancouver, BC")
        self.assertIsNone(normalized.country_evidence)
        self.assertIsNone(normalized.workplace_evidence)
        self.assertEqual(normalized.description_text, "")

    def test_requires_nonblank_stable_posting_id(self):
        for value in (None, "", "   "):
            with self.subTest(value=value):
                payload = self.representative_payload()
                payload["id"] = value

                with self.assertRaisesMessage(
                    NormalizationError,
                    "Lever field 'id' must be a nonblank string.",
                ):
                    normalize_lever_posting(
                        payload,
                        company_name="Example Company",
                    )

    def test_rejects_invalid_required_fields_with_field_specific_errors(self):
        cases = (
            ("text", None, "Lever field 'text' must be a nonblank string."),
            (
                "hostedUrl",
                "/jobs/posting-123",
                "Lever field 'hostedUrl' must be an absolute HTTP(S) URL.",
            ),
            (
                "applyUrl",
                123,
                "Lever field 'applyUrl' must be a nonblank string.",
            ),
        )

        for field_name, value, message in cases:
            with self.subTest(field_name=field_name):
                payload = self.representative_payload()
                payload[field_name] = value

                with self.assertRaisesMessage(NormalizationError, message):
                    normalize_lever_posting(
                        payload,
                        company_name="Example Company",
                    )

    def test_requires_company_snapshot(self):
        with self.assertRaisesMessage(
            NormalizationError,
            "company_name must be a nonblank string.",
        ):
            normalize_lever_posting(
                self.representative_payload(),
                company_name=" ",
            )

    def test_rejects_invalid_list_content(self):
        payload = self.representative_payload()
        payload["lists"] = [{"content": ["not", "html"]}]

        with self.assertRaisesMessage(
            NormalizationError,
            "Lever field 'lists[0].content' must be a string or null.",
        ):
            normalize_lever_posting(
                payload,
                company_name="Example Company",
            )

    def test_ignores_script_and_style_content(self):
        payload = self.representative_payload()
        payload["descriptionPlain"] = None
        payload["lists"] = [
            {
                "content": (
                    "<p>Visible before.</p>"
                    "<script>window.hiddenScript = true;</script>"
                    "<style>.hidden-style { display: none; }</style>"
                    "<p>Visible after.</p>"
                )
            }
        ]
        payload["additionalPlain"] = None

        normalized = normalize_lever_posting(
            payload,
            company_name="Example Company",
        )

        self.assertEqual(
            normalized.description_text,
            "Visible before.\n\nVisible after.",
        )
        self.assertNotIn("hiddenScript", normalized.description_text)
        self.assertNotIn("hidden-style", normalized.description_text)

    def test_rejects_non_json_payload_values(self):
        payload = self.representative_payload()
        payload["unexpected"] = math.nan

        with self.assertRaisesMessage(
            NormalizationError,
            "Lever payload must contain only JSON-compatible values.",
        ):
            normalize_lever_posting(
                payload,
                company_name="Example Company",
            )
