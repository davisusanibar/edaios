"""Adapter degradable para la API HTTP local de Engram.

No importa código Engram ni lo convierte en dependencia. El daemon se gestiona
fuera de Core. Deliberadamente no se implementan operaciones de gobierno.
"""
from __future__ import annotations

import hashlib
import json
import re
import socket
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


CLAIM_BOUNDARY = (
    "provider externo de local-working memory; no es autoridad, aprobación, "
    "evidencia ni promoción EDAIOS"
)

PROVIDER_ID = "engram-http-local"
DEFAULT_PROVIDER_RELEASE = "1.19.0"
DEFAULT_API_HEALTH_VERSION = "0.1.0"
_ALLOWED_SENSITIVITY = frozenset({"T0", "T1"})
_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EngramAdapterError(ValueError):
    """Configuración o respuesta Engram incompatible."""


class EngramClientError(EngramAdapterError):
    """Engram rechazó la petición (4xx): error del caller, no del provider."""


class ProviderUnavailable(EngramAdapterError):
    """El runtime opcional no está disponible en loopback."""


class _RejectRedirects(HTTPRedirectHandler):
    """Impide que headers o payload local salgan por un redirect HTTP."""

    def redirect_request(self, *_args: Any, **_kwargs: Any) -> None:
        raise EngramAdapterError("redirect Engram rechazado")


def _open_loopback(request: Request, timeout: float) -> Any:
    return build_opener(_RejectRedirects()).open(request, timeout=timeout)


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EngramAdapterError(f"{field} es obligatorio")
    normalized = value.strip()
    if "\n" in normalized or "\r" in normalized:
        raise EngramAdapterError(f"{field} debe ocupar una sola línea")
    return normalized


def _sensitivity(value: str) -> str:
    if value not in _ALLOWED_SENSITIVITY:
        raise EngramAdapterError("Engram adapter rechaza T2/T3 sin decisión de privacidad")
    return value


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _source_digest(value: str | None, *, fallback: Any) -> str:
    if value is None:
        return _canonical_digest(fallback)
    if not isinstance(value, str):
        raise EngramAdapterError("source_digest debe ser SHA-256")
    normalized = value.removeprefix("sha256:").lower()
    if not _SHA256.fullmatch(normalized):
        raise EngramAdapterError("source_digest debe ser SHA-256")
    return "sha256:" + normalized


def _list_payload(payload: Any, *, key: str, context: str) -> list[Any]:
    """Engram serializa slices Go vacíos como ``null``; se normaliza a lista."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        values = payload.get(key)
        if values is None:
            return []
        if isinstance(values, list):
            return values
    raise EngramAdapterError(f"{context} no contiene lista")


def _http_error_detail(exc: HTTPError) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8", errors="strict"))
    except (OSError, ValueError, UnicodeDecodeError):
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("error"), str):
        return payload["error"]
    return exc.reason if isinstance(exc.reason, str) else str(exc)


@dataclass(frozen=True)
class EngramHTTPProvider:
    base_url: str = "http://127.0.0.1:7437"
    provider_release: str = DEFAULT_PROVIDER_RELEASE
    required_api_version: str = DEFAULT_API_HEALTH_VERSION
    # Alias transitorio para consumidores 3.1 tempranos. Cuando se declara,
    # fija explícitamente el valor del campo health.version; no representa el
    # release del proveedor.
    required_version: str | None = None
    token: str | None = None
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme != "http":
            raise EngramAdapterError("Engram solo admite HTTP loopback")
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise EngramAdapterError("endpoint Engram no loopback rechazado")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise EngramAdapterError("endpoint Engram contiene credenciales o query")
        if parsed.path not in {"", "/"}:
            raise EngramAdapterError("endpoint Engram debe apuntar al root")
        if not _SEMVER.fullmatch(self.provider_release):
            raise EngramAdapterError("provider_release debe ser una versión semántica")
        if not _SEMVER.fullmatch(self.required_api_version):
            raise EngramAdapterError("required_api_version debe ser una versión semántica")
        if self.required_version is not None and not _SEMVER.fullmatch(self.required_version):
            raise EngramAdapterError("required_version debe ser una versión semántica")
        if self.timeout_seconds <= 0 or self.timeout_seconds > 30:
            raise EngramAdapterError("timeout_seconds fuera de rango")

    @property
    def endpoint(self) -> str:
        return self.base_url.rstrip("/")

    @property
    def expected_api_version(self) -> str:
        """Versión del contrato HTTP, nunca el release de instalación."""

        return self.required_version or self.required_api_version

    def capabilities(self) -> dict[str, Any]:
        return {
            "schema": "edaios.memory-provider-capabilities/v1",
            "provider": PROVIDER_ID,
            "provider_version": self.provider_release,
            "provider_release": self.provider_release,
            "required_api_version": self.expected_api_version,
            "channel": "local-working",
            "operations": [
                "health", "search", "context", "save-observation",
                "session-start", "session-end", "timeline",
                "conflict-candidates-read",
            ],
            "forbidden_operations": [
                "approve", "cloud", "compare", "decide", "delete", "judge",
                "promote", "remote-sync", "write-canonical",
            ],
            "allowed_sensitivity": sorted(_ALLOWED_SENSITIVITY),
            "authoritative": False,
            "rebuildable": True,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        if not path.startswith("/") or ".." in path:
            raise EngramAdapterError("path de API inválido")
        url = self.endpoint + path
        if query:
            url += "?" + urlencode(
                {key: value for key, value in query.items() if value is not None}
            )
        data = json.dumps(body, ensure_ascii=True).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with _open_loopback(request, self.timeout_seconds) as response:
                final_url = response.geturl() if hasattr(response, "geturl") else url
                final_host = urlparse(final_url).hostname
                if final_host not in {"127.0.0.1", "localhost", "::1"}:
                    raise EngramAdapterError("redirect Engram fuera de loopback rechazado")
                raw = response.read()
        except HTTPError as exc:
            # 4xx es un error de petición del caller, no degradación del provider.
            if 400 <= exc.code < 500:
                raise EngramClientError(
                    f"Engram rechazó la petición ({exc.code}): {_http_error_detail(exc)}"
                ) from exc
            raise ProviderUnavailable(f"Engram no disponible: {exc}") from exc
        except (URLError, TimeoutError, socket.timeout, OSError) as exc:
            raise ProviderUnavailable(f"Engram no disponible: {exc}") from exc
        try:
            return json.loads(raw.decode("utf-8", errors="strict")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EngramAdapterError("respuesta Engram no es JSON UTF-8") from exc

    def _bounded(
        self,
        payload: Any,
        *,
        operation: str,
        sensitivity: str,
        source_ref: str,
        source_digest: str | None = None,
        observed_api_version: str | None = None,
    ) -> dict[str, Any]:
        normalized_sensitivity = _sensitivity(sensitivity)
        normalized_source_ref = _required_text(source_ref, "source_ref")
        normalized_source_digest = _source_digest(source_digest, fallback=payload)
        return {
            "schema": "edaios.external-memory-result/v1",
            "operation": operation,
            "provider": PROVIDER_ID,
            "provider_version": self.provider_release,
            "provider_release": self.provider_release,
            "provider_api_version": observed_api_version,
            "channel": "local-working",
            "sensitivity": normalized_sensitivity,
            "source_ref": normalized_source_ref,
            "source_digest": normalized_source_digest,
            "provenance": {
                "source_ref": normalized_source_ref,
                "source_digest": normalized_source_digest,
                "provider": PROVIDER_ID,
                "provider_release": self.provider_release,
                "api_health_version": observed_api_version,
                "preservation": "adapter-envelope",
            },
            "authoritative": False,
            "rebuildable": True,
            "claim_boundary": CLAIM_BOUNDARY,
            "result": payload,
        }

    def _health_result(
        self,
        *,
        status: str,
        reason: str,
        reported_version: str | None,
        observed_api_version: str | None,
        compatibility_basis: str,
    ) -> dict[str, Any]:
        source_ref = f"{self.endpoint}/health"
        source_payload = {
            "status": status,
            "reported_version": reported_version,
            "reason": reason,
        }
        return {
            "schema": "edaios.memory-provider-health/v1",
            "status": status,
            "provider": PROVIDER_ID,
            "provider_version": self.provider_release,
            "provider_release": self.provider_release,
            "required_api_version": self.expected_api_version,
            "reported_health_version": reported_version,
            "observed_api_version": observed_api_version,
            "compatibility_basis": compatibility_basis,
            "channel": "local-working",
            "sensitivity": "T0",
            "source_ref": source_ref,
            "source_digest": _canonical_digest(source_payload),
            "provenance": {
                "source_ref": source_ref,
                "source_digest": _canonical_digest(source_payload),
                "provider": PROVIDER_ID,
                "provider_release": self.provider_release,
                "api_health_version": observed_api_version,
                "preservation": "adapter-envelope",
            },
            "authoritative": False,
            "rebuildable": True,
            "reason": reason,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def health(self) -> dict[str, Any]:
        try:
            payload = self._request("GET", "/health")
        except ProviderUnavailable as exc:
            return self._health_result(
                status="degraded",
                reason=str(exc),
                reported_version=None,
                observed_api_version=None,
                compatibility_basis="provider-unavailable",
            )
        except EngramClientError as exc:
            return self._health_result(
                status="incompatible",
                reason=str(exc),
                reported_version=None,
                observed_api_version=None,
                compatibility_basis="health-response-invalid",
            )
        if (
            not isinstance(payload, dict)
            or payload.get("status") != "ok"
            or payload.get("service") != "engram"
        ):
            reported = payload.get("version") if isinstance(payload, dict) else None
            return self._health_result(
                status="incompatible",
                reason="health response no identifica status=ok y service=engram",
                reported_version=str(reported) if reported is not None else None,
                observed_api_version=None,
                compatibility_basis="service-and-status",
            )
        observed = str(payload.get("version", ""))
        if observed == self.expected_api_version:
            return self._health_result(
                status="ok",
                reason="contrato HTTP compatible",
                reported_version=observed,
                observed_api_version=observed,
                compatibility_basis="api-health-version",
            )
        return self._health_result(
            status="incompatible",
            reason="versión del contrato HTTP incompatible",
            reported_version=observed,
            observed_api_version=None,
            compatibility_basis="api-health-version",
        )

    def _require_compatible(self) -> dict[str, Any]:
        health = self.health()
        if health["status"] != "ok":
            raise ProviderUnavailable(
                f"Engram {health['status']}: API requerida {self.expected_api_version}, "
                f"health reportado {health.get('reported_health_version', 'unavailable')}"
            )
        return health

    def search(
        self,
        query: str,
        *,
        project: str | None = None,
        limit: int = 10,
        sensitivity: str = "T0",
    ) -> list[dict[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            raise EngramAdapterError("query no puede estar vacío")
        if not 1 <= limit <= 100:
            raise EngramAdapterError("limit fuera de rango")
        normalized_sensitivity = _sensitivity(sensitivity)
        health = self._require_compatible()
        payload = self._request(
            "GET", "/search", query={"q": query.strip(), "project": project, "limit": limit}
        )
        values = _list_payload(payload, key="results", context="search response")
        return [
            self._bounded(
                value,
                operation="search",
                sensitivity=normalized_sensitivity,
                source_ref=f"{self.endpoint}/search",
                observed_api_version=health.get("observed_api_version"),
            )
            for value in values
        ]

    def get_context(
        self,
        *,
        project: str | None = None,
        scope: str | None = None,
        sensitivity: str = "T0",
    ) -> dict[str, Any]:
        """Bloque de contexto agregado del proyecto (GET /context, solo lectura)."""
        normalized_sensitivity = _sensitivity(sensitivity)
        if scope is not None and scope not in {"project", "personal", "global"}:
            raise EngramAdapterError("scope debe ser project, personal o global")
        health = self._require_compatible()
        payload = self._request(
            "GET", "/context", query={"project": project, "scope": scope}
        )
        context_text = ""
        if isinstance(payload, dict):
            value = payload.get("context")
            context_text = value if isinstance(value, str) else ""
        return self._bounded(
            {"context": context_text, "project": project, "scope": scope},
            operation="context",
            sensitivity=normalized_sensitivity,
            source_ref=f"{self.endpoint}/context",
            observed_api_version=health.get("observed_api_version"),
        )

    def save_observation(
        self,
        *,
        session_id: str,
        project: str,
        subject: str,
        claim: str,
        value: str,
        record_type: str = "discovery",
        sensitivity: str = "T0",
        source_ref: str = "edaios-core",
        source_digest: str | None = None,
        **_ignored: Any,
    ) -> dict[str, Any]:
        normalized_sensitivity = _sensitivity(sensitivity)
        for field, item in {
            "session_id": session_id, "project": project, "subject": subject,
            "claim": claim, "value": value, "record_type": record_type,
        }.items():
            if not isinstance(item, str) or not item.strip():
                raise EngramAdapterError(f"{field} es obligatorio")
        normalized_source_ref = _required_text(source_ref, "source_ref")
        normalized_source_digest = _source_digest(
            source_digest,
            fallback={"source_ref": normalized_source_ref, "value": value},
        )
        health = self._require_compatible()
        payload = self._request(
            "POST",
            "/observations",
            body={
                "session_id": session_id,
                "project": project,
                "type": record_type,
                "title": f"{subject}: {claim}",
                "content": value,
                "tool_name": normalized_source_ref,
                "scope": "project",
            },
        )
        return self._bounded(
            payload,
            operation="save-observation",
            sensitivity=normalized_sensitivity,
            source_ref=normalized_source_ref,
            source_digest=normalized_source_digest,
            observed_api_version=health.get("observed_api_version"),
        )

    def start_session(
        self,
        *,
        session_id: str,
        project: str,
        worktree: str,
        sensitivity: str = "T0",
        source_ref: str = "engram-session-start",
        source_digest: str | None = None,
        **_ignored: Any,
    ) -> dict[str, Any]:
        normalized_sensitivity = _sensitivity(sensitivity)
        session_id = _required_text(session_id, "session_id")
        project = _required_text(project, "project")
        worktree = _required_text(worktree, "worktree")
        source_ref = _required_text(source_ref, "source_ref")
        health = self._require_compatible()
        request_body = {"id": session_id, "project": project, "directory": worktree}
        payload = self._request(
            "POST", "/sessions",
            body=request_body,
        )
        return self._bounded(
            payload,
            operation="session-start",
            sensitivity=normalized_sensitivity,
            source_ref=source_ref,
            source_digest=_source_digest(source_digest, fallback=request_body),
            observed_api_version=health.get("observed_api_version"),
        )

    def end_session(
        self,
        session_id: str,
        *,
        summary: str,
        sensitivity: str = "T0",
        source_ref: str = "engram-session-summary",
        source_digest: str | None = None,
        **_ignored: Any,
    ) -> dict[str, Any]:
        normalized_sensitivity = _sensitivity(sensitivity)
        session_id = _required_text(session_id, "session_id")
        summary = _required_text(summary, "summary")
        source_ref = _required_text(source_ref, "source_ref")
        health = self._require_compatible()
        request_body = {"summary": summary}
        payload = self._request(
            "POST", f"/sessions/{quote(session_id, safe='')}/end", body=request_body
        )
        return self._bounded(
            payload,
            operation="session-end",
            sensitivity=normalized_sensitivity,
            source_ref=source_ref,
            source_digest=_source_digest(source_digest, fallback=request_body),
            observed_api_version=health.get("observed_api_version"),
        )

    def timeline(
        self, session_id: str, *, sensitivity: str = "T0", limit: int = 100
    ) -> list[dict[str, Any]]:
        """Observaciones de la sesión, filtradas en el adapter.

        Engram v1.19.0 no expone listado de observaciones por sesión:
        GET /sessions/{id} devuelve solo metadatos. Se valida la sesión,
        se listan las observaciones recientes de su proyecto y se filtra
        por session_id; la cobertura queda acotada por ``limit``.
        """
        normalized_sensitivity = _sensitivity(sensitivity)
        session_id = _required_text(session_id, "session_id")
        if not 1 <= limit <= 500:
            raise EngramAdapterError("limit fuera de rango")
        health = self._require_compatible()
        session_path = f"/sessions/{quote(session_id, safe='')}"
        session = self._request("GET", session_path)
        if not isinstance(session, dict):
            raise EngramAdapterError("session response inválida")
        observations = self._request(
            "GET", "/observations",
            query={"project": session.get("project"), "limit": limit},
        )
        values = _list_payload(
            observations, key="observations", context="observations response"
        )
        return [
            self._bounded(
                value,
                operation="timeline",
                sensitivity=normalized_sensitivity,
                source_ref=f"{self.endpoint}{session_path}",
                observed_api_version=health.get("observed_api_version"),
            )
            for value in values
            if isinstance(value, dict) and value.get("session_id") == session_id
        ]

    def conflict_candidates(
        self, *, project: str | None = None, sensitivity: str = "T0"
    ) -> list[dict[str, Any]]:
        normalized_sensitivity = _sensitivity(sensitivity)
        health = self._require_compatible()
        payload = self._request(
            "GET", "/conflicts", query={"project": project, "status": "pending", "limit": 100}
        )
        values = _list_payload(payload, key="relations", context="conflicts response")
        return [
            self._bounded(
                value,
                operation="conflict-candidates-read",
                sensitivity=normalized_sensitivity,
                source_ref=f"{self.endpoint}/conflicts",
                observed_api_version=health.get("observed_api_version"),
            )
            for value in values
        ]


__all__ = [
    "EngramAdapterError",
    "EngramClientError",
    "EngramHTTPProvider",
    "ProviderUnavailable",
]
