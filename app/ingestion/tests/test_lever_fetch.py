import ssl
from email.message import Message
from http.client import IncompleteRead
from unittest.mock import call, patch
from urllib.error import HTTPError, URLError

from django.test import SimpleTestCase

from ingestion.adapters.lever_fetch import LeverFetchError, fetch_lever_postings


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self) -> bytes:
        return self.body


class _IncompleteResponse(_FakeResponse):
    def __init__(self) -> None:
        super().__init__(b"")

    def read(self) -> bytes:
        raise IncompleteRead(b"partial", 100)


def _http_error(status_code: int, retry_after: str | None = None) -> HTTPError:
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return HTTPError(
        "https://api.lever.co/v0/postings/example?mode=json",
        status_code,
        "Test response",
        headers,
        None,
    )


class FetchLeverPostingsTests(SimpleTestCase):
    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_builds_global_url_and_returns_raw_postings(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(
            b'[{"id": "posting-1", "nested": {"value": true}}]'
        )

        postings = fetch_lever_postings(
            board_identifier=" example/board ",
            api_instance="global",
        )

        self.assertEqual(
            postings,
            [{"id": "posting-1", "nested": {"value": True}}],
        )
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://api.lever.co/v0/postings/example%2Fboard?mode=json",
        )
        self.assertEqual(request.get_header("Accept"), "application/json")
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 10.0)

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_builds_eu_url_and_uses_configured_timeout(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(b"[]")

        postings = fetch_lever_postings(
            board_identifier="example board",
            api_instance="eu",
            timeout_seconds=4.5,
        )

        self.assertEqual(postings, [])
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://api.eu.lever.co/v0/postings/example%20board?mode=json",
        )
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 4.5)

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_rejects_malformed_json_without_retrying(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(b"{")

        with self.assertRaisesMessage(
            LeverFetchError,
            "Response was not valid JSON",
        ) as context:
            fetch_lever_postings(
                board_identifier="example",
                api_instance="global",
            )

        self.assertEqual(context.exception.attempts, 1)
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_requires_top_level_list(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(b'{"id": "posting-1"}')

        with self.assertRaisesMessage(
            LeverFetchError,
            "JSON response must be a top-level list; received dict.",
        ):
            fetch_lever_postings(
                board_identifier="example",
                api_instance="global",
            )

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_requires_each_list_item_to_be_an_object(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(b'[{"id": "posting-1"}, null]')

        with self.assertRaisesMessage(
            LeverFetchError,
            "JSON response item 1 must be an object; received NoneType.",
        ):
            fetch_lever_postings(
                board_identifier="example",
                api_instance="global",
            )

    @patch("ingestion.adapters.lever_fetch.time.sleep")
    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_retries_timeouts_and_connection_failures(
        self,
        mock_urlopen,
        mock_sleep,
    ):
        mock_urlopen.side_effect = [
            TimeoutError("timed out"),
            URLError("connection reset"),
            _FakeResponse(b"[]"),
        ]

        postings = fetch_lever_postings(
            board_identifier="example",
            api_instance="global",
            timeout_seconds=3,
        )

        self.assertEqual(postings, [])
        self.assertEqual(mock_urlopen.call_count, 3)
        self.assertEqual(
            [item.kwargs["timeout"] for item in mock_urlopen.call_args_list],
            [3.0, 3.0, 3.0],
        )
        self.assertEqual(mock_sleep.call_args_list, [call(1.0), call(2.0)])

    @patch("ingestion.adapters.lever_fetch.time.sleep")
    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_retries_incomplete_response_read(self, mock_urlopen, mock_sleep):
        mock_urlopen.side_effect = [
            _IncompleteResponse(),
            _FakeResponse(b'[{"id": "posting-1"}]'),
        ]

        postings = fetch_lever_postings(
            board_identifier="example",
            api_instance="global",
        )

        self.assertEqual(postings, [{"id": "posting-1"}])
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_called_once_with(1.0)

    @patch("ingestion.adapters.lever_fetch.time.sleep")
    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_raises_contextual_error_after_transport_retries_are_exhausted(
        self,
        mock_urlopen,
        mock_sleep,
    ):
        mock_urlopen.side_effect = URLError("connection refused")

        with self.assertRaises(LeverFetchError) as context:
            fetch_lever_postings(
                board_identifier="example",
                api_instance="global",
            )

        error = context.exception
        self.assertEqual(error.board_identifier, "example")
        self.assertEqual(error.api_instance, "global")
        self.assertEqual(error.attempts, 3)
        self.assertIsNone(error.status_code)
        self.assertIn("api.lever.co", error.url or "")
        self.assertEqual(mock_urlopen.call_count, 3)
        self.assertEqual(mock_sleep.call_args_list, [call(1.0), call(2.0)])

    @patch("ingestion.adapters.lever_fetch.time.sleep")
    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_does_not_retry_identifiable_certificate_validation_failure(
        self,
        mock_urlopen,
        mock_sleep,
    ):
        certificate_error = ssl.SSLCertVerificationError(
            1,
            "certificate verify failed",
        )
        mock_urlopen.side_effect = URLError(certificate_error)

        with self.assertRaisesMessage(
            LeverFetchError,
            "TLS certificate validation failed",
        ):
            fetch_lever_postings(
                board_identifier="example",
                api_instance="global",
            )

        self.assertEqual(mock_urlopen.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("ingestion.adapters.lever_fetch.time.sleep")
    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_retries_429_using_delta_seconds_retry_after(
        self,
        mock_urlopen,
        mock_sleep,
    ):
        mock_urlopen.side_effect = [
            _http_error(429, "7"),
            _FakeResponse(b"[]"),
        ]

        postings = fetch_lever_postings(
            board_identifier="example",
            api_instance="global",
        )

        self.assertEqual(postings, [])
        mock_sleep.assert_called_once_with(7.0)

    @patch("ingestion.adapters.lever_fetch.time.sleep")
    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_caps_http_date_retry_after_at_sixty_seconds(
        self,
        mock_urlopen,
        mock_sleep,
    ):
        mock_urlopen.side_effect = [
            _http_error(503, "Wed, 21 Oct 2099 07:28:00 GMT"),
            _FakeResponse(b"[]"),
        ]

        postings = fetch_lever_postings(
            board_identifier="example",
            api_instance="global",
        )

        self.assertEqual(postings, [])
        mock_sleep.assert_called_once_with(60.0)

    def test_invalid_expired_and_negative_retry_after_use_fallback(self):
        retry_after_values = (
            "later",
            "Wed, 21 Oct 2000 07:28:00 GMT",
            "-1",
        )

        for retry_after in retry_after_values:
            with self.subTest(retry_after=retry_after):
                with (
                    patch(
                        "ingestion.adapters.lever_fetch.urlopen",
                        side_effect=[
                            _http_error(429, retry_after),
                            _FakeResponse(b"[]"),
                        ],
                    ),
                    patch("ingestion.adapters.lever_fetch.time.sleep") as mock_sleep,
                ):
                    postings = fetch_lever_postings(
                        board_identifier="example",
                        api_instance="global",
                    )

                self.assertEqual(postings, [])
                mock_sleep.assert_called_once_with(1.0)

    @patch("ingestion.adapters.lever_fetch.time.sleep")
    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_retries_5xx_and_reports_final_status(
        self,
        mock_urlopen,
        mock_sleep,
    ):
        mock_urlopen.side_effect = [
            _http_error(500),
            _http_error(502),
            _http_error(599),
        ]

        with self.assertRaises(LeverFetchError) as context:
            fetch_lever_postings(
                board_identifier="example",
                api_instance="global",
            )

        self.assertEqual(context.exception.status_code, 599)
        self.assertEqual(context.exception.attempts, 3)
        self.assertEqual(mock_sleep.call_args_list, [call(1.0), call(2.0)])

    @patch("ingestion.adapters.lever_fetch.time.sleep")
    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_does_not_retry_other_4xx_responses(self, mock_urlopen, mock_sleep):
        mock_urlopen.side_effect = _http_error(404)

        with self.assertRaises(LeverFetchError) as context:
            fetch_lever_postings(
                board_identifier="retired-board",
                api_instance="eu",
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.attempts, 1)
        self.assertEqual(mock_urlopen.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("ingestion.adapters.lever_fetch.urlopen")
    def test_rejects_invalid_configuration_before_request(self, mock_urlopen):
        cases = (
            ({"board_identifier": " ", "api_instance": "global"}, "Board identifier"),
            ({"board_identifier": "example", "api_instance": "US"}, "API instance"),
            (
                {
                    "board_identifier": "example",
                    "api_instance": "global",
                    "timeout_seconds": 0,
                },
                "Timeout",
            ),
        )

        for arguments, message in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaisesMessage(LeverFetchError, message):
                    fetch_lever_postings(**arguments)

        mock_urlopen.assert_not_called()
