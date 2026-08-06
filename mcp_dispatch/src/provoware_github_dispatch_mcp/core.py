from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator

REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORKFLOW_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+\.(?:yml|yaml)$")
Scalar = str | bool | int | float


class PolicyError(ValueError):
    """Raised when a dispatch request violates the local allowlist."""


class InputRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    required: bool = False
    pattern: str | None = None
    min_length: int = Field(default=0, ge=0, le=4096)
    max_length: int = Field(default=1024, ge=1, le=4096)

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, value: str | None) -> str | None:
        if value is not None:
            re.compile(value)
        return value

    def validate_value(self, key: str, value: Scalar) -> Scalar:
        rendered = str(value)
        if not self.min_length <= len(rendered) <= self.max_length:
            raise PolicyError(
                f"Input {key!r} verletzt die erlaubte Länge "
                f"({self.min_length}..{self.max_length})."
            )
        if self.pattern is not None and re.fullmatch(self.pattern, rendered) is None:
            raise PolicyError(f"Input {key!r} verletzt das konfigurierte Format.")
        return value


class WorkflowRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inputs: dict[str, InputRule] = Field(default_factory=dict)
    deny_unknown_inputs: bool = True


class RepositoryRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflows: dict[str, WorkflowRule]


class DispatchAllowlist(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = Field(default=1, ge=1, le=1)
    repositories: dict[str, RepositoryRule]

    @field_validator("repositories")
    @classmethod
    def validate_repositories(
        cls, value: dict[str, RepositoryRule]
    ) -> dict[str, RepositoryRule]:
        for repository, repository_rule in value.items():
            if REPOSITORY_PATTERN.fullmatch(repository) is None:
                raise ValueError(f"Ungültiger Repositoryname in Allowlist: {repository!r}")
            for workflow in repository_rule.workflows:
                if WORKFLOW_PATTERN.fullmatch(workflow) is None:
                    raise ValueError(f"Ungültiger Workflowname in Allowlist: {workflow!r}")
        return value

    @classmethod
    def from_path(cls, path: Path) -> DispatchAllowlist:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise PolicyError(f"Allowlist fehlt: {path}") from exc
        except json.JSONDecodeError as exc:
            raise PolicyError(f"Allowlist ist kein gültiges JSON: {path}: {exc}") from exc
        return cls.model_validate(payload)

    def validate_dispatch(
        self,
        repository: str,
        workflow: str,
        inputs: dict[str, Scalar],
    ) -> dict[str, Scalar]:
        if REPOSITORY_PATTERN.fullmatch(repository) is None:
            raise PolicyError("Repository muss exakt owner/name entsprechen.")
        if WORKFLOW_PATTERN.fullmatch(workflow) is None:
            raise PolicyError("Workflow muss ein einfacher .yml- oder .yaml-Dateiname sein.")

        repository_rule = self.repositories.get(repository)
        if repository_rule is None:
            raise PolicyError(f"Repository ist nicht freigegeben: {repository}")
        workflow_rule = repository_rule.workflows.get(workflow)
        if workflow_rule is None:
            raise PolicyError(f"Workflow ist nicht freigegeben: {repository}/{workflow}")

        unknown = sorted(set(inputs) - set(workflow_rule.inputs))
        if unknown and workflow_rule.deny_unknown_inputs:
            raise PolicyError(f"Nicht freigegebene Inputs: {', '.join(unknown)}")

        missing = sorted(
            key
            for key, rule in workflow_rule.inputs.items()
            if rule.required and key not in inputs
        )
        if missing:
            raise PolicyError(f"Erforderliche Inputs fehlen: {', '.join(missing)}")

        validated: dict[str, Scalar] = {}
        for key, value in inputs.items():
            if not isinstance(value, (str, bool, int, float)):
                raise PolicyError(f"Input {key!r} muss ein skalarer JSON-Wert sein.")
            rule = workflow_rule.inputs.get(key)
            if rule is None:
                if workflow_rule.deny_unknown_inputs:
                    raise PolicyError(f"Input ist nicht freigegeben: {key}")
                validated[key] = value
            else:
                validated[key] = rule.validate_value(key, value)
        return validated


def redact_inputs(inputs: dict[str, Any]) -> dict[str, str]:
    """Return metadata only; input values never leave the service response/logs."""
    return {key: type(value).__name__ for key, value in sorted(inputs.items())}


API_VERSION = "2026-03-10"
FIXED_API_URL = "https://api.github.com"


class GitHubApiError(RuntimeError):
    """Raised for a rejected or inconsistent GitHub API operation."""


@dataclass(frozen=True, slots=True)
class DispatchReceipt:
    accepted: bool
    repository: str
    workflow: str
    ref: str
    main_sha: str
    status_code: int
    workflow_run_id: int | None = None
    run_url: str | None = None
    html_url: str | None = None


class GitHubActionsClient:
    def __init__(
        self,
        token: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        if not token or token.isspace():
            raise GitHubApiError("GITHUB_TOKEN fehlt oder ist leer.")
        self._client = httpx.AsyncClient(
            base_url=FIXED_API_URL,
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
            transport=transport,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "provoware-github-dispatch-mcp/0.1.0",
                "X-GitHub-Api-Version": API_VERSION,
            },
        )

    async def __aenter__(self) -> GitHubActionsClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _json_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        expected: set[int],
    ) -> tuple[httpx.Response, dict[str, Any] | None]:
        response = await self._client.request(method, url, params=params, json=json_body)
        if response.status_code not in expected:
            request_id = response.headers.get("x-github-request-id", "unbekannt")
            raise GitHubApiError(
                f"GitHub API verweigerte {method} {url}: HTTP {response.status_code}; "
                f"Request-ID {request_id}."
            )
        if not response.content:
            return response, None
        try:
            payload = response.json()
        except ValueError as exc:
            raise GitHubApiError("GitHub lieferte eine ungültige JSON-Antwort.") from exc
        if not isinstance(payload, dict):
            raise GitHubApiError("GitHub lieferte unerwartete Antwortdaten.")
        return response, payload

    async def dispatch_on_main(
        self,
        repository: str,
        workflow: str,
        inputs: dict[str, str | bool | int | float],
    ) -> DispatchReceipt:
        owner, repo = repository.split("/", 1)
        owner_q = quote(owner, safe="")
        repo_q = quote(repo, safe="")
        workflow_q = quote(workflow, safe="")

        _, branch = await self._json_request(
            "GET",
            f"/repos/{owner_q}/{repo_q}/branches/main",
            expected={200},
        )
        assert branch is not None
        main_sha = branch.get("commit", {}).get("sha")
        if not isinstance(main_sha, str) or len(main_sha) != 40:
            raise GitHubApiError("main konnte nicht als unveränderlicher Commit aufgelöst werden.")

        await self._json_request(
            "GET",
            f"/repos/{owner_q}/{repo_q}/contents/.github/workflows/{workflow_q}",
            params={"ref": "main"},
            expected={200},
        )
        _, workflow_metadata = await self._json_request(
            "GET",
            f"/repos/{owner_q}/{repo_q}/actions/workflows/{workflow_q}",
            expected={200},
        )
        assert workflow_metadata is not None
        if workflow_metadata.get("state") != "active":
            raise GitHubApiError("Der freigegebene Workflow ist nicht aktiv.")
        if workflow_metadata.get("path") != f".github/workflows/{workflow}":
            raise GitHubApiError("GitHub meldet einen unerwarteten Workflowpfad.")

        response, payload = await self._json_request(
            "POST",
            f"/repos/{owner_q}/{repo_q}/actions/workflows/{workflow_q}/dispatches",
            json_body={"ref": "main", "inputs": inputs},
            expected={200, 204},
        )
        payload = payload or {}
        run_id = payload.get("workflow_run_id")
        if run_id is not None and not isinstance(run_id, int):
            raise GitHubApiError("GitHub lieferte eine ungültige Workflow-Run-ID.")
        return DispatchReceipt(
            accepted=True,
            repository=repository,
            workflow=workflow,
            ref="main",
            main_sha=main_sha,
            status_code=response.status_code,
            workflow_run_id=run_id,
            run_url=payload.get("run_url") if isinstance(payload.get("run_url"), str) else None,
            html_url=payload.get("html_url") if isinstance(payload.get("html_url"), str) else None,
        )


class DispatchService:
    def __init__(self, allowlist: DispatchAllowlist, client: GitHubActionsClient) -> None:
        self._allowlist = allowlist
        self._client = client

    async def dispatch_workflow_on_main(
        self,
        repository: str,
        workflow: str,
        inputs: dict[str, Scalar],
    ) -> dict[str, object]:
        validated = self._allowlist.validate_dispatch(repository, workflow, inputs)
        receipt = await self._client.dispatch_on_main(repository, workflow, validated)
        result = asdict(receipt)
        result["input_schema"] = redact_inputs(validated)
        result["safety_contract"] = {
            "ref_is_fixed": True,
            "fixed_ref": "main",
            "repository_allowlisted": True,
            "workflow_allowlisted": True,
            "unknown_inputs_denied": True,
            "input_values_redacted": True,
        }
        return result
