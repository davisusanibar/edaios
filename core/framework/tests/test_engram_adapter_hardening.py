import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from edaios_memory_adapter import (
    EngramAdapterError,
    EngramClientError,
    EngramHTTPProvider,
    ProviderUnavailable,
)


class _Response:
    def __init__(self, value, url="http://127.0.0.1:7437/health"):
        self.raw = json.dumps(value).encode("utf-8")
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.raw

    def geturl(self):
        return self.url


def _api_010(request, timeout):
    del timeout
    if request.full_url.endswith("/health"):
        return _Response({"status": "ok", "service": "engram", "version": "0.1.0"})
    if request.method == "POST":
        return _Response(
            {"accepted": True, "body": json.loads(request.data or b"{}")},
            url=request.full_url,
        )
    return _Response({"results": [{"id": 7, "title": "memory"}]}, url=request.full_url)


def _engram_v1_19(request, timeout):
    """Réplica de las respuestas reales del server Go de engram v1.19.0."""
    del timeout
    url = request.full_url
    if url.endswith("/health"):
        return _Response({"status": "ok", "service": "engram", "version": "0.1.0"})
    if "/sessions/" in url and request.method == "GET":
        # GET /sessions/{id} devuelve solo metadatos, sin observations.
        return _Response(
            {
                "id": "session-1",
                "project": "alpha",
                "directory": "/work/alpha",
                "started_at": "2026-07-16T00:00:00Z",
            },
            url=url,
        )
    if url.rstrip("?").endswith("/context") or "/context?" in url:
        return _Response({"context": "contexto agregado"}, url=url)
    if "/observations" in url and request.method == "GET":
        return _Response(
            [
                {"id": 1, "session_id": "session-1", "title": "primera"},
                {"id": 2, "session_id": "other-session", "title": "ajena"},
                {"id": 3, "session_id": "session-1", "title": "segunda"},
            ],
            url=url,
        )
    if "/search" in url:
        # Slice Go nil sin matches: el server serializa null.
        return _Response(None, url=url)
    if request.method == "POST":
        return _Response(
            {"id": 9, "status": "saved", "body": json.loads(request.data or b"{}")},
            url=url,
        )
    return _Response({}, url=url)


def _http_error(request, code, message):
    return HTTPError(
        request.full_url,
        code,
        "error",
        {},
        io.BytesIO(json.dumps({"error": message}).encode("utf-8")),
    )


class EngramAdapterHardeningTest(unittest.TestCase):
    def test_health_separates_provider_release_from_api_version(self):
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=_api_010):
            health = EngramHTTPProvider().health()

        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["provider_version"], "1.19.0")
        self.assertEqual(health["provider_release"], "1.19.0")
        self.assertEqual(health["required_api_version"], "0.1.0")
        self.assertEqual(health["observed_api_version"], "0.1.0")
        self.assertEqual(health["compatibility_basis"], "api-health-version")

    def test_incompatible_api_version_fails_closed(self):
        def incompatible(request, timeout):
            del request, timeout
            return _Response({"status": "ok", "service": "engram", "version": "0.2.0"})

        provider = EngramHTTPProvider()
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=incompatible):
            self.assertEqual(provider.health()["status"], "incompatible")
            with self.assertRaisesRegex(EngramAdapterError, "API requerida 0.1.0"):
                provider.search("memory")

    def test_redirect_handler_rejects_redirects(self):
        handler = __import__(
            "edaios_memory_adapter.engram", fromlist=["_RejectRedirects"]
        )._RejectRedirects()
        with self.assertRaisesRegex(EngramAdapterError, "redirect Engram rechazado"):
            handler.redirect_request()

    def test_result_preserves_sensitivity_and_source_provenance(self):
        digest = "sha256:" + "a" * 64
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=_api_010):
            result = EngramHTTPProvider().save_observation(
                session_id="session-1",
                project="alpha",
                subject="orders",
                claim="backend",
                value="RocksDB",
                sensitivity="T1",
                source_ref="specs/007/evidence/source.md",
                source_digest=digest,
            )

        self.assertEqual(result["provider_version"], "1.19.0")
        self.assertEqual(result["provider_release"], "1.19.0")
        self.assertEqual(result["provider_api_version"], "0.1.0")
        self.assertEqual(result["sensitivity"], "T1")
        self.assertEqual(result["source_ref"], "specs/007/evidence/source.md")
        self.assertEqual(result["source_digest"], digest)
        self.assertEqual(result["provenance"]["source_ref"], result["source_ref"])
        self.assertEqual(result["provenance"]["source_digest"], digest)
        self.assertEqual(result["provenance"]["preservation"], "adapter-envelope")

    def test_search_with_null_payload_returns_empty_list(self):
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=_engram_v1_19):
            self.assertEqual(EngramHTTPProvider().search("nada"), [])

    def test_timeline_filters_project_observations_by_session(self):
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=_engram_v1_19):
            timeline = EngramHTTPProvider().timeline("session-1")

        self.assertEqual(len(timeline), 2)
        self.assertEqual(
            [entry["result"]["title"] for entry in timeline], ["primera", "segunda"]
        )
        for entry in timeline:
            self.assertEqual(entry["operation"], "timeline")
            self.assertEqual(entry["result"]["session_id"], "session-1")
            self.assertFalse(entry["authoritative"])

    def test_timeline_with_null_observations_returns_empty_list(self):
        def null_observations(request, timeout):
            if "/observations" in request.full_url and request.method == "GET":
                return _Response(None, url=request.full_url)
            return _engram_v1_19(request, timeout)

        with patch(
            "edaios_memory_adapter.engram._open_loopback", side_effect=null_observations
        ):
            self.assertEqual(EngramHTTPProvider().timeline("session-1"), [])

    def test_session_chain_start_save_end(self):
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=_engram_v1_19):
            provider = EngramHTTPProvider()
            started = provider.start_session(
                session_id="session-1", project="alpha", worktree="/work/alpha"
            )
            saved = provider.save_observation(
                session_id="session-1",
                project="alpha",
                subject="orders",
                claim="backend",
                value="RocksDB",
            )
            ended = provider.end_session("session-1", summary="cierre")

        self.assertEqual(started["operation"], "session-start")
        self.assertEqual(started["result"]["body"]["id"], "session-1")
        self.assertEqual(saved["operation"], "save-observation")
        self.assertEqual(saved["result"]["body"]["session_id"], "session-1")
        self.assertEqual(ended["operation"], "session-end")
        self.assertEqual(ended["result"]["body"]["summary"], "cierre")
        for envelope in (started, saved, ended):
            self.assertEqual(envelope["channel"], "local-working")
            self.assertFalse(envelope["authoritative"])
            self.assertEqual(envelope["provider_api_version"], "0.1.0")

    def test_client_error_is_not_reported_as_unavailable(self):
        def bad_request(request, timeout):
            del timeout
            if request.full_url.endswith("/health"):
                return _Response({"status": "ok", "service": "engram", "version": "0.1.0"})
            raise _http_error(request, 400, "session_id is required")

        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=bad_request):
            with self.assertRaisesRegex(
                EngramClientError, r"400.*session_id is required"
            ) as ctx:
                EngramHTTPProvider().save_observation(
                    session_id="session-1",
                    project="alpha",
                    subject="orders",
                    claim="backend",
                    value="RocksDB",
                )
        self.assertNotIsInstance(ctx.exception, ProviderUnavailable)

    def test_server_error_raises_provider_unavailable(self):
        def server_error(request, timeout):
            del timeout
            raise _http_error(request, 500, "boom")

        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=server_error):
            with self.assertRaises(ProviderUnavailable):
                EngramHTTPProvider().search("memoria")

    def test_connection_refused_raises_provider_unavailable(self):
        def refused(request, timeout):
            del request, timeout
            raise URLError("connection refused")

        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=refused):
            with self.assertRaises(ProviderUnavailable):
                EngramHTTPProvider().search("memoria")

    def test_health_reports_incompatible_on_client_error(self):
        def not_engram(request, timeout):
            del timeout
            raise _http_error(request, 404, "not found")

        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=not_engram):
            health = EngramHTTPProvider().health()

        self.assertEqual(health["status"], "incompatible")
        self.assertEqual(health["compatibility_basis"], "health-response-invalid")

    def test_t3_sensitivity_is_rejected(self):
        with self.assertRaisesRegex(EngramAdapterError, "T2/T3"):
            EngramHTTPProvider().search("memoria", sensitivity="T3")

    def test_get_context_returns_read_only_envelope(self):
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=_engram_v1_19):
            envelope = EngramHTTPProvider().get_context(project="alpha", scope="project")

        self.assertEqual(envelope["operation"], "context")
        self.assertEqual(envelope["result"]["context"], "contexto agregado")
        self.assertFalse(envelope["authoritative"])
        self.assertEqual(envelope["provider_api_version"], "0.1.0")


if __name__ == "__main__":
    unittest.main()
