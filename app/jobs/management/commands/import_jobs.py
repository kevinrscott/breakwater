from django.core.management.base import BaseCommand, CommandError

from ingestion.services import import_lever_source
from jobs.models import EmployerSource


class Command(BaseCommand):
    help = "Import jobs from configured active Lever employer sources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-id",
            type=int,
            help="Import one active Lever EmployerSource by database ID.",
        )

    def handle(self, *args, **options):
        source_id = options["source_id"]
        sources = EmployerSource.objects.filter(
            is_active=True,
            source_type="LEVER",
        )
        if source_id is not None:
            sources = sources.filter(pk=source_id)

        selected_sources = list(
            sources.order_by("company_name", "board_identifier", "pk")
        )
        if not selected_sources:
            if source_id is None:
                raise CommandError("No active Lever employer sources are configured.")
            raise CommandError(
                f"EmployerSource {source_id} is not an active Lever source."
            )

        totals = {
            "fetched": 0,
            "created": 0,
            "changed": 0,
            "unchanged": 0,
            "reactivated": 0,
        }
        succeeded = 0
        failed = 0

        for source in selected_sources:
            context = f"{source.company_name} [{source.board_identifier}]"
            try:
                result = import_lever_source(source)
            except Exception as exc:
                failed += 1
                detail = " ".join(str(exc).split()) or "No error message provided."
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed {context}: {type(exc).__name__}: {detail}"
                    )
                )
                continue

            succeeded += 1
            for field in totals:
                totals[field] += getattr(result, field)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported {context}: "
                    f"fetched={result.fetched} "
                    f"created={result.created} "
                    f"changed={result.changed} "
                    f"unchanged={result.unchanged} "
                    f"reactivated={result.reactivated}"
                )
            )

        attempted = len(selected_sources)
        self.stdout.write(
            "Import summary: "
            f"attempted={attempted} "
            f"succeeded={succeeded} "
            f"failed={failed} "
            f"fetched={totals['fetched']} "
            f"created={totals['created']} "
            f"changed={totals['changed']} "
            f"unchanged={totals['unchanged']} "
            f"reactivated={totals['reactivated']}"
        )

        if failed:
            raise CommandError(
                f"{failed} of {attempted} Lever source imports failed."
            )
