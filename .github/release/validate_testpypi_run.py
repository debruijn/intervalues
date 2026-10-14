"""Require a successful TestPyPI upload run before promoting its artifacts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import PurePosixPath
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PUBLISH_WORKFLOW = ".github/workflows/publish-release.yml"
TESTPYPI_JOB = "Publish validated artifacts to TestPyPI"


def validate_run(run: dict[str, object], jobs: list[dict[str, object]]) -> None:
    workflow_path = str(run.get("path", "")).split("@", maxsplit=1)[0]
    if workflow_path != PUBLISH_WORKFLOW:
        raise ValueError("The source run did not use the release publishing workflow")
    if run.get("event") != "workflow_dispatch" or run.get("head_branch") != "main":
        raise ValueError("The source run must be manually dispatched from main")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ValueError("The source release workflow run did not complete successfully")
    if not any(
        job.get("name") == TESTPYPI_JOB and job.get("conclusion") == "success"
        for job in jobs
    ):
        raise ValueError("The source run did not successfully publish to TestPyPI")


def _get_json(url: str, token: str) -> dict[str, object]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"GitHub API request failed with HTTP {exc.code}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"GitHub API returned an unexpected response from {url}")
    return payload


def validate_testpypi_run(run_id: str, repository: str, token: str) -> None:
    if re.fullmatch(r"[0-9]+", run_id) is None:
        raise ValueError("TestPyPI workflow run ID must contain only digits")
    repo_path = PurePosixPath(repository)
    if len(repo_path.parts) != 2 or any(part in {".", ".."} for part in repo_path.parts):
        raise ValueError(f"Invalid GitHub repository name: {repository}")

    api_root = f"https://api.github.com/repos/{repository}/actions/runs/{run_id}"
    run = _get_json(api_root, token)
    jobs_url = f"{api_root}/jobs?{urlencode({'per_page': 100})}"
    jobs_response = _get_json(jobs_url, token)
    jobs = jobs_response.get("jobs")
    if not isinstance(jobs, list) or not all(isinstance(job, dict) for job in jobs):
        raise ValueError("GitHub API returned an invalid workflow jobs list")
    validate_run(run, jobs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("repository")
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise ValueError("GH_TOKEN is required to verify a TestPyPI workflow run")
    validate_testpypi_run(args.run_id, args.repository, token)
    print(f"Verified successful TestPyPI run {args.run_id}")


if __name__ == "__main__":
    main()
