import os
import re

import httpx
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
print(GITHUB_TOKEN)

GITHUB_API = "https://api.github.com"


def parse_pr_url(pr_url: str):
    pattern = (
        r"^https?://github\.com/"
        r"([^/]+)/([^/]+)/pull/(\d+)/?$"
    )

    match = re.match(pattern, pr_url.strip())

    if not match:
        raise ValueError("Invalid GitHub Pull Request URL")

    return {
        "owner": match.group(1),
        "repo": match.group(2),
        "pr_number": int(match.group(3))
    }


async def fetch_pull_request(owner, repo, pr_number):

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async with httpx.AsyncClient(
        headers=headers,
        timeout=30.0,
        follow_redirects=True
    ) as client:

        # Fetch PR metadata
        pr_response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
        )

        pr_response.raise_for_status()

        pr = pr_response.json()

        # Fetch changed files
        files = []
        page = 1

        while True:

            files_response = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                params={
                    "per_page": 100,
                    "page": page
                }
            )

            files_response.raise_for_status()

            page_files = files_response.json()

            files.extend(page_files)

            if len(page_files) < 100 or page >= 30:
                break

            page += 1

    return {
        "repository": f"{owner}/{repo}",
        "pr_number": pr["number"],
        "title": pr["title"],
        "description": pr["body"],
        "state": pr["state"],
        "draft": pr["draft"],
        "author": pr["user"]["login"],
        "html_url": pr["html_url"],
        "base_branch": pr["base"]["ref"],
        "head_branch": pr["head"]["ref"],
        "commits": pr["commits"],
        "changed_files": pr["changed_files"],
        "additions": pr["additions"],
        "deletions": pr["deletions"],
        "files": [
            {
                "filename": file["filename"],
                "status": file["status"],
                "additions": file["additions"],
                "deletions": file["deletions"],
                "changes": file["changes"],
                "patch": file.get("patch"),
                "blob_url": file["blob_url"],
                "raw_url": file["raw_url"]
            }
            for file in files
        ]
    }