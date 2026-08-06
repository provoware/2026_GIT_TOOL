from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from provoware_github_dispatch_mcp.core import (
    DispatchAllowlist,
    DispatchReceipt,
    DispatchService,
    GitHubActionsClient,
    GitHubApiError,
    PolicyError,
)

REPO = "provoware/PROVOWARE_VIDEO_AUTOMATION_2026"
WORKFLOW = "kubuntu-pr-validation.yml"
SHA = "a" * 40


def policy() -> DispatchAllowlist:
    return DispatchAllowlist.model_validate(
        {
            "schema_version": 1,
            "repositories": {
                REPO: {
                    "workflows": {
                        WORKFLOW: {
                            "deny_unknown_inputs": True,
                            "inputs": {
                                "pr_number": {"required": True, "pattern": "^[1-9][0-9]*$"},
                                "base_sha": {
                                    "required": True,
                                    "pattern": "^[0-9a-f]{40}$",
                                    "min_length": 40,
                                    "max_length": 40,
                                },
                            },
                        }
                    }
                }
            },
        }
    )


def test_allowlisted_dispatch_is_accepted() -> None:
    assert policy().validate_dispatch(
        REPO, WORKFLOW, {"pr_number": "64", "base_sha": SHA}
    ) == {"pr_number": "64", "base_sha": SHA}


@pytest.mark.parametrize(
    ("repository", "workflow", "inputs"),
    [
        ("other/repo", WORKFLOW, {"pr_number": "64", "base_sha": SHA}),
        (REPO, "other.yml", {"pr_number": "64", "base_sha": SHA}),
        (REPO, WORKFLOW, {"pr_number": "64", "base_sha": SHA, "extra": "x"}),
        (REPO, WORKFLOW, {"pr_number": "64"}),
        (REPO, WORKFLOW, {"pr_number": "64", "base_sha": "not-a-sha"}),
        (REPO, "../danger.yml", {}),
    ],
)
def test_policy_rejects_every_unapproved_dimension(
    repository: str, workflow: str, inputs: dict[str, str]
) -> None:
    with pytest.raises(PolicyError):
        policy().validate_dispatch(repository, workflow, inputs)


def test_dispatch_is_forced_to_main_and_preflighted() -> None:
    seen: list[tuple[str, str, dict[str, object] | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content) if request.content else None
        seen.append((request.method, str(request.url), payload))
        path = request.url.path
        if path.endswith("/branches/main"):
            return httpx.Response(200, json={"commit": {"sha": SHA}})
        if "/contents/.github/workflows/" in path:
            assert request.url.params["ref"] == "main"
            return httpx.Response(200, json={"path": f".github/workflows/{WORKFLOW}"})
        if path.endswith(f"/actions/workflows/{WORKFLOW}"):
            return httpx.Response(
                200,
                json={"state": "active", "path": f".github/workflows/{WORKFLOW}"},
            )
        if path.endswith(f"/actions/workflows/{WORKFLOW}/dispatches"):
            assert payload == {"ref": "main", "inputs": {"pr_number": "64"}}
            return httpx.Response(200, json={"workflow_run_id": 123})
        raise AssertionError(path)

    async def run() -> None:
        async with GitHubActionsClient(
            "secret", transport=httpx.MockTransport(handler)
        ) as client:
            receipt = await client.dispatch_on_main(REPO, WORKFLOW, {"pr_number": "64"})
            assert receipt.ref == "main"
            assert receipt.workflow_run_id == 123

    asyncio.run(run())
    assert [method for method, _, _ in seen] == ["GET", "GET", "GET", "POST"]


def test_inactive_workflow_fails_before_dispatch() -> None:
    methods: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        methods.append(request.method)
        path = request.url.path
        if path.endswith("/branches/main"):
            return httpx.Response(200, json={"commit": {"sha": SHA}})
        if "/contents/.github/workflows/" in path:
            return httpx.Response(200, json={})
        return httpx.Response(
            200,
            json={"state": "disabled_manually", "path": f".github/workflows/{WORKFLOW}"},
        )

    async def run() -> None:
        async with GitHubActionsClient(
            "secret", transport=httpx.MockTransport(handler)
        ) as client:
            with pytest.raises(GitHubApiError, match="nicht aktiv"):
                await client.dispatch_on_main(REPO, WORKFLOW, {})

    asyncio.run(run())
    assert methods == ["GET", "GET", "GET"]


class FakeClient:
    async def dispatch_on_main(self, repository: str, workflow: str, inputs: dict):
        assert inputs == {"pr_number": "64", "base_sha": SHA}
        return DispatchReceipt(
            accepted=True,
            repository=repository,
            workflow=workflow,
            ref="main",
            main_sha=SHA,
            status_code=204,
        )


def test_service_redacts_values_and_reports_contract() -> None:
    async def run() -> None:
        result = await DispatchService(policy(), FakeClient()).dispatch_workflow_on_main(
            REPO, WORKFLOW, {"pr_number": "64", "base_sha": SHA}
        )
        assert result["ref"] == "main"
        assert result["input_schema"] == {"base_sha": "str", "pr_number": "str"}
        assert "64" not in str(result["input_schema"])
        assert result["safety_contract"]["ref_is_fixed"] is True

    asyncio.run(run())
