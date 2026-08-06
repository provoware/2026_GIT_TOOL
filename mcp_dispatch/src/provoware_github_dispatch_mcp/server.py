from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from .core import (
    DispatchAllowlist,
    DispatchService,
    GitHubActionsClient,
    PolicyError,
    Scalar,
)

mcp = MCPServer(
    "Provoware GitHub Workflow Dispatch",
    instructions=(
        "Exposes exactly one fail-closed tool. It can dispatch only allowlisted existing "
        "GitHub Actions workflows and always uses the main branch."
    ),
)


def _allowlist_path() -> Path:
    return Path(os.environ.get("GITHUB_DISPATCH_ALLOWLIST", "config/dispatch_allowlist.json"))


@mcp.tool()
async def dispatch_workflow_on_main(
    repository: str,
    workflow: str,
    inputs: dict[str, Scalar],
) -> dict[str, Any]:
    """Dispatch one allowlisted existing GitHub Actions workflow on main.

    The ref is intentionally not an argument. Unknown repositories, workflows, inputs,
    malformed SHA values and inactive workflows are rejected before the dispatch request.
    """
    token = os.environ.get("GITHUB_TOKEN", "")
    try:
        allowlist = DispatchAllowlist.from_path(_allowlist_path())
        async with GitHubActionsClient(token) as client:
            service = DispatchService(allowlist, client)
            return await service.dispatch_workflow_on_main(repository, workflow, inputs)
    except (PolicyError, ValueError) as exc:
        raise ValueError(f"Dispatch verweigert: {exc}") from exc


def main() -> None:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8000"))
    mcp.run(
        "streamable-http",
        host=host,
        port=port,
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()
