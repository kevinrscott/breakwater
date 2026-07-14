import json
import math
import ssl
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.client import HTTPException
from typing import Literal, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from ingestion.types import RawJob

_BASE_URLS = {
    "global": "https://api.lever.co/v0/postings",
    "eu": "https://api.eu.lever.co/v0/postings",
}
_DEFAULT_TIMEOUT_SECONDS = 10.0
_MAX_ATTEMPTS = 3
_FALLBACK_RETRY_DELAYS = (1.0, 2.0)
_MAX_RETRY_AFTER_SECONDS = 60.0


class LeverFetchError(RuntimeError):
    """Raised when postings cannot be fetched safely from a Lever board."""

    def __init__(
        self,
        detail: str,
        *,
        board_identifier: str,
        api_instance: str,
        url: str | None,
        attempts: int,
        status_code: int | None = None,
    ) -> None:
        self.detail = detail
        self.board_identifier = board_identifier
        self.api_instance = api_instance
        self.url = url
        self.attempts = attempts
        self.status_code = status_code

        context = [
            f"board={board_identifier!r}",
            f"api_instance={api_instance!r}",
            f"attempts={attempts}",
        ]
        if url is not None:
            context.append(f"url={url!r}")
        if status_code is not None:
            context.append(f"status_code={status_code}")

        super().__init__(f"Lever fetch failed ({', '.join(context)}): {detail}")


def fetch_lever_postings(
    *,
    board_identifier: str,
    api_instance: Literal["global", "eu"],
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
) -> list[RawJob]:
    """Fetch and validate raw JSON postings from one Lever employer board."""
    board = _validate_board_identifier(board_identifier, api_instance)
    instance = _validate_api_instance(api_instance, board)
    timeout = _validate_timeout(timeout_seconds, board, instance)
    url = _build_url(board, instance)
    request = Request(
        url,
        headers={"Accept": "application/json"},
        method="GET",
    )

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                response_body = response.read()
        except HTTPError as exc:
            retry_after = (
                exc.headers.get("Retry-After") if exc.headers is not None else None
            )
            if exc.fp is not None:
                exc.close()

            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if retryable and attempt < _MAX_ATTEMPTS:
                time.sleep(_retry_delay(attempt, retry_after))
                continue

            reason = f" {exc.reason}" if exc.reason else ""
            raise LeverFetchError(
                f"HTTP {exc.code}{reason}.",
                board_identifier=board,
                api_instance=instance,
                url=url,
                attempts=attempt,
                status_code=exc.code,
            ) from exc
        except ssl.SSLCertVerificationError as exc:
            raise LeverFetchError(
                f"TLS certificate validation failed: {exc}.",
                board_identifier=board,
                api_instance=instance,
                url=url,
                attempts=attempt,
            ) from exc
        except (URLError, TimeoutError, ConnectionError, HTTPException) as exc:
            if _is_certificate_validation_error(exc):
                raise LeverFetchError(
                    f"TLS certificate validation failed: {exc}.",
                    board_identifier=board,
                    api_instance=instance,
                    url=url,
                    attempts=attempt,
                ) from exc

            if attempt < _MAX_ATTEMPTS:
                time.sleep(_fallback_retry_delay(attempt))
                continue

            raise LeverFetchError(
                f"Request failed: {exc}.",
                board_identifier=board,
                api_instance=instance,
                url=url,
                attempts=attempt,
            ) from exc

        return _decode_and_validate_response(
            response_body,
            board_identifier=board,
            api_instance=instance,
            url=url,
            attempts=attempt,
        )

    raise AssertionError("Lever retry loop exited unexpectedly.")


def _validate_board_identifier(board_identifier: str, api_instance: object) -> str:
    if not isinstance(board_identifier, str) or not board_identifier.strip():
        raise LeverFetchError(
            "Board identifier must be a nonblank string.",
            board_identifier=(
                board_identifier
                if isinstance(board_identifier, str)
                else repr(board_identifier)
            ),
            api_instance=(
                api_instance
                if isinstance(api_instance, str)
                else repr(api_instance)
            ),
            url=None,
            attempts=0,
        )
    return board_identifier.strip()


def _validate_api_instance(api_instance: object, board_identifier: str) -> str:
    if not isinstance(api_instance, str) or api_instance not in _BASE_URLS:
        raise LeverFetchError(
            "API instance must be 'global' or 'eu'.",
            board_identifier=board_identifier,
            api_instance=(
                api_instance
                if isinstance(api_instance, str)
                else repr(api_instance)
            ),
            url=None,
            attempts=0,
        )
    return api_instance


def _validate_timeout(
    timeout_seconds: object,
    board_identifier: str,
    api_instance: str,
) -> float:
    if isinstance(timeout_seconds, bool):
        timeout = math.nan
    else:
        try:
            timeout = float(timeout_seconds)
        except (TypeError, ValueError):
            timeout = math.nan

    if not math.isfinite(timeout) or timeout <= 0:
        raise LeverFetchError(
            "Timeout must be a positive finite number of seconds.",
            board_identifier=board_identifier,
            api_instance=api_instance,
            url=None,
            attempts=0,
        )
    return timeout


def _build_url(board_identifier: str, api_instance: str) -> str:
    board_path = quote(board_identifier, safe="")
    query = urlencode({"mode": "json"})
    return f"{_BASE_URLS[api_instance]}/{board_path}?{query}"


def _retry_delay(attempt: int, retry_after: object) -> float:
    parsed_delay = _parse_retry_after(retry_after)
    if parsed_delay is not None:
        return min(parsed_delay, _MAX_RETRY_AFTER_SECONDS)
    return _fallback_retry_delay(attempt)


def _fallback_retry_delay(attempt: int) -> float:
    return _FALLBACK_RETRY_DELAYS[attempt - 1]


def _parse_retry_after(value: object) -> float | None:
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    if normalized.isascii() and normalized.isdigit():
        return float(normalized)

    try:
        retry_at = parsedate_to_datetime(normalized)
    except (TypeError, ValueError, OverflowError):
        return None

    if retry_at.tzinfo is None:
        return None

    delay = (
        retry_at.astimezone(timezone.utc) - datetime.now(timezone.utc)
    ).total_seconds()
    if delay <= 0:
        return None
    return delay


def _is_certificate_validation_error(exc: BaseException) -> bool:
    if isinstance(exc, ssl.SSLCertVerificationError):
        return True
    reason = getattr(exc, "reason", None)
    return isinstance(reason, ssl.SSLCertVerificationError)


def _decode_and_validate_response(
    response_body: bytes,
    *,
    board_identifier: str,
    api_instance: str,
    url: str,
    attempts: int,
) -> list[RawJob]:
    try:
        decoded = json.loads(response_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LeverFetchError(
            f"Response was not valid JSON: {exc}.",
            board_identifier=board_identifier,
            api_instance=api_instance,
            url=url,
            attempts=attempts,
        ) from exc

    if not isinstance(decoded, list):
        raise LeverFetchError(
            "JSON response must be a top-level list; "
            f"received {type(decoded).__name__}.",
            board_identifier=board_identifier,
            api_instance=api_instance,
            url=url,
            attempts=attempts,
        )

    for index, posting in enumerate(decoded):
        if not isinstance(posting, dict):
            raise LeverFetchError(
                f"JSON response item {index} must be an object; "
                f"received {type(posting).__name__}.",
                board_identifier=board_identifier,
                api_instance=api_instance,
                url=url,
                attempts=attempts,
            )

    return cast(list[RawJob], decoded)
