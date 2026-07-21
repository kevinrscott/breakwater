from io import StringIO
from unittest.mock import call, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from ingestion.services import LeverImportResult
from jobs.models import EmployerSource


def _result(
    *,
    fetched=0,
    created=0,
    changed=0,
    unchanged=0,
    reactivated=0,
):
    return LeverImportResult(
        fetched=fetched,
        created=created,
        changed=changed,
        unchanged=unchanged,
        reactivated=reactivated,
    )


class ImportJobsCommandTests(TestCase):
    def create_source(self, **overrides):
        sequence = EmployerSource.objects.count() + 1
        values = {
            "company_name": f"Employer {sequence}",
            "source_type": "LEVER",
            "api_instance": "global",
            "board_identifier": f"employer-{sequence}",
            "careers_url": f"https://jobs.example.com/employer-{sequence}",
            "is_active": True,
        }
        values.update(overrides)
        return EmployerSource.objects.create(**values)

    @patch("jobs.management.commands.import_jobs.import_lever_source")
    def test_imports_active_lever_sources_in_deterministic_order(self, mock_import):
        last_source = self.create_source(
            company_name="Zeta Company",
            board_identifier="zeta-board",
        )
        middle_source = self.create_source(
            company_name="Alpha Company",
            board_identifier="second-board",
        )
        first_source = self.create_source(
            company_name="Alpha Company",
            board_identifier="first-board",
        )
        self.create_source(
            company_name="Inactive Company",
            board_identifier="inactive-board",
            is_active=False,
        )
        self.create_source(
            company_name="Other Provider",
            source_type="GREENHOUSE",
            board_identifier="other-board",
        )
        mock_import.side_effect = [
            _result(fetched=1, created=1),
            _result(fetched=2, changed=1, unchanged=1),
            _result(fetched=3, created=2, unchanged=1, reactivated=1),
        ]
        stdout = StringIO()

        call_command("import_jobs", stdout=stdout)

        self.assertEqual(
            mock_import.call_args_list,
            [call(first_source), call(middle_source), call(last_source)],
        )
        output = stdout.getvalue()
        self.assertIn("Imported Alpha Company [first-board]", output)
        self.assertIn(
            "fetched=1 created=1 changed=0 unchanged=0 reactivated=0",
            output,
        )
        self.assertIn("Imported Alpha Company [second-board]", output)
        self.assertIn("Imported Zeta Company [zeta-board]", output)
        self.assertIn(
            "Import summary: attempted=3 succeeded=3 failed=0 "
            "fetched=6 created=3 changed=1 unchanged=2 reactivated=1",
            output,
        )

    @patch("jobs.management.commands.import_jobs.import_lever_source")
    def test_source_id_imports_only_requested_active_lever_source(self, mock_import):
        selected_source = self.create_source(company_name="Selected Company")
        self.create_source(company_name="Other Company")
        mock_import.return_value = _result(fetched=4, unchanged=4)
        stdout = StringIO()

        call_command(
            "import_jobs",
            source_id=selected_source.pk,
            stdout=stdout,
        )

        mock_import.assert_called_once_with(selected_source)
        self.assertIn("attempted=1 succeeded=1 failed=0", stdout.getvalue())

    @patch("jobs.management.commands.import_jobs.import_lever_source")
    def test_no_active_lever_sources_fails_without_importing(self, mock_import):
        self.create_source(is_active=False)
        self.create_source(source_type="GREENHOUSE")

        with self.assertRaisesMessage(
            CommandError,
            "No active Lever employer sources are configured.",
        ):
            call_command("import_jobs")

        mock_import.assert_not_called()

    @patch("jobs.management.commands.import_jobs.import_lever_source")
    def test_ineligible_source_id_fails_without_fallback_import(self, mock_import):
        active_source = self.create_source()
        inactive_source = self.create_source(is_active=False)
        other_provider = self.create_source(source_type="GREENHOUSE")

        for source_id in (999999, inactive_source.pk, other_provider.pk):
            with self.subTest(source_id=source_id):
                with self.assertRaisesMessage(
                    CommandError,
                    f"EmployerSource {source_id} is not an active Lever source.",
                ):
                    call_command("import_jobs", source_id=source_id)

        mock_import.assert_not_called()
        self.assertTrue(active_source.is_active)

    @patch("jobs.management.commands.import_jobs.import_lever_source")
    def test_failure_does_not_prevent_later_sources_and_exits_after_summary(
        self,
        mock_import,
    ):
        first_source = self.create_source(
            company_name="Alpha Company",
            board_identifier="alpha-board",
        )
        failed_source = self.create_source(
            company_name="Bravo Company",
            board_identifier="bravo-board",
        )
        last_source = self.create_source(
            company_name="Charlie Company",
            board_identifier="charlie-board",
        )
        mock_import.side_effect = [
            _result(fetched=2, created=1, unchanged=1),
            RuntimeError("synthetic source failure"),
            _result(fetched=3, changed=2, reactivated=1),
        ]
        stdout = StringIO()
        stderr = StringIO()

        with self.assertRaisesMessage(
            CommandError,
            "1 of 3 Lever source imports failed.",
        ):
            call_command("import_jobs", stdout=stdout, stderr=stderr)

        self.assertEqual(
            mock_import.call_args_list,
            [call(first_source), call(failed_source), call(last_source)],
        )
        self.assertIn("Imported Charlie Company [charlie-board]", stdout.getvalue())
        self.assertIn(
            "Import summary: attempted=3 succeeded=2 failed=1 "
            "fetched=5 created=1 changed=2 unchanged=1 reactivated=1",
            stdout.getvalue(),
        )
        self.assertIn(
            "Failed Bravo Company [bravo-board]: RuntimeError: "
            "synthetic source failure",
            stderr.getvalue(),
        )
