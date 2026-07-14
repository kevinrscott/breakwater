import json
from collections.abc import Mapping
from html.parser import HTMLParser
from typing import cast
from urllib.parse import urlsplit

from ingestion.normalization import NormalizationError
from ingestion.types import JSONValue, NormalizedJobInput, RawJob

_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "div",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "ol",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}
_IGNORED_TAGS = {"script", "style"}


class _PlainTextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_element_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag in _IGNORED_TAGS:
            self.ignored_element_depth += 1
            return
        if self.ignored_element_depth:
            return
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _IGNORED_TAGS:
            if self.ignored_element_depth:
                self.ignored_element_depth -= 1
            return
        if self.ignored_element_depth:
            return
        if tag in _BLOCK_TAGS and tag != "br":
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignored_element_depth:
            self.parts.append(data)


def normalize_lever_posting(
    raw_posting: RawJob,
    *,
    company_name: str,
) -> NormalizedJobInput:
    """Normalize one Lever posting without fetching or persisting it."""
    raw_payload = _copy_json_payload(raw_posting)
    source_job_id = _required_string(raw_payload, "id")
    title = _required_string(raw_payload, "text")
    company_snapshot = _required_value(company_name, "company_name")
    source_url = _required_url(raw_payload, "hostedUrl")
    application_url = _required_url(raw_payload, "applyUrl")
    categories = _optional_mapping(raw_payload, "categories")

    location_text = _location_text(categories)
    country_evidence = _optional_string(raw_payload, "country")
    workplace_evidence = _optional_string(raw_payload, "workplaceType")
    description_text = _description_text(raw_payload)

    return NormalizedJobInput(
        source_job_id=source_job_id,
        title=title,
        company_name=company_snapshot,
        source_url=source_url,
        application_url=application_url,
        location_text=location_text,
        country_evidence=country_evidence,
        workplace_evidence=workplace_evidence,
        description_text=description_text,
        raw_payload=raw_payload,
    )


def _copy_json_payload(raw_posting: RawJob) -> dict[str, JSONValue]:
    if not isinstance(raw_posting, Mapping):
        raise NormalizationError("Lever payload must be a JSON-compatible mapping.")
    if any(not isinstance(key, str) for key in raw_posting):
        raise NormalizationError("Lever payload keys must be strings.")

    try:
        serialized = json.dumps(dict(raw_posting), allow_nan=False)
        payload = json.loads(serialized)
    except (TypeError, ValueError) as exc:
        raise NormalizationError(
            "Lever payload must contain only JSON-compatible values."
        ) from exc

    return cast(dict[str, JSONValue], payload)


def _required_string(payload: Mapping[str, JSONValue], field_name: str) -> str:
    return _required_value(payload.get(field_name), f"Lever field '{field_name}'")


def _required_value(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NormalizationError(f"{field_name} must be a nonblank string.")
    return value.strip()


def _required_url(payload: Mapping[str, JSONValue], field_name: str) -> str:
    value = _required_string(payload, field_name)
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise NormalizationError(
            f"Lever field '{field_name}' must be an absolute HTTP(S) URL."
        )
    return value


def _optional_mapping(
    payload: Mapping[str, JSONValue],
    field_name: str,
) -> Mapping[str, JSONValue]:
    value = payload.get(field_name)
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise NormalizationError(f"Lever field '{field_name}' must be an object.")
    return value


def _optional_string(
    payload: Mapping[str, JSONValue],
    field_name: str,
    *,
    field_path: str | None = None,
) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        label = field_path or field_name
        raise NormalizationError(
            f"Lever field '{label}' must be a string or null."
        )
    return value.strip() or None


def _location_text(categories: Mapping[str, JSONValue]) -> str:
    all_locations = categories.get("allLocations")
    if all_locations is not None:
        if not isinstance(all_locations, list):
            raise NormalizationError(
                "Lever field 'categories.allLocations' must be an array or null."
            )

        locations: list[str] = []
        for index, location in enumerate(all_locations):
            if not isinstance(location, str):
                raise NormalizationError(
                    "Lever field "
                    f"'categories.allLocations[{index}]' must be a string."
                )
            normalized = _normalize_plain_text(location)
            if normalized and normalized not in locations:
                locations.append(normalized)
        if locations:
            return "; ".join(locations)

    primary_location = _optional_string(
        categories,
        "location",
        field_path="categories.location",
    )
    return _normalize_plain_text(primary_location or "")


def _description_text(payload: Mapping[str, JSONValue]) -> str:
    sections: list[str] = []

    description = _optional_string(payload, "descriptionPlain")
    if description:
        sections.append(_normalize_plain_text(description))

    lists = payload.get("lists")
    if lists is not None:
        if not isinstance(lists, list):
            raise NormalizationError("Lever field 'lists' must be an array or null.")
        for index, item in enumerate(lists):
            if not isinstance(item, Mapping):
                raise NormalizationError(
                    f"Lever field 'lists[{index}]' must be an object."
                )
            content = _optional_string(
                item,
                "content",
                field_path=f"lists[{index}].content",
            )
            if content:
                plain_content = _html_to_text(content)
                if plain_content:
                    sections.append(plain_content)

    additional = _optional_string(payload, "additionalPlain")
    if additional:
        sections.append(_normalize_plain_text(additional))

    return "\n\n".join(section for section in sections if section)


def _html_to_text(value: str) -> str:
    parser = _PlainTextHTMLParser()
    parser.feed(value)
    parser.close()
    return _normalize_plain_text("".join(parser.parts))


def _normalize_plain_text(value: str) -> str:
    normalized_lines: list[str] = []
    blank_line_pending = False

    for raw_line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = " ".join(raw_line.replace("\xa0", " ").split())
        if not line:
            if normalized_lines:
                blank_line_pending = True
            continue
        if blank_line_pending:
            normalized_lines.append("")
            blank_line_pending = False
        normalized_lines.append(line)

    return "\n".join(normalized_lines)
