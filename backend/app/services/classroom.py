"""GitHub Classroom API client (read-only).

Docs: https://docs.github.com/en/rest/classroom
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

CLASSROOM_API = "https://api.github.com"


@dataclass
class ClassroomInfo:
    id: int
    name: str
    url: str


@dataclass
class AssignmentInfo:
    id: int
    title: str
    slug: str
    invite_link: str
    classroom_id: int
    classroom_url: str = ""


async def list_classrooms(admin_token: str) -> list[ClassroomInfo]:
    """List all GitHub Classrooms accessible to the authenticated user."""
    results: list[ClassroomInfo] = []
    page = 1
    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            resp = await client.get(
                f"{CLASSROOM_API}/classrooms",
                headers={
                    "Authorization": f"Bearer {admin_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"per_page": 100, "page": page},
            )
            if resp.status_code != 200:
                logger.warning("Failed to list classrooms: %s %s", resp.status_code, resp.text)
                break
            data = resp.json()
            if not data:
                break
            for c in data:
                results.append(ClassroomInfo(id=c["id"], name=c["name"], url=c.get("url", "")))
            if len(data) < 100:
                break
            page += 1
    return results


async def list_assignments(admin_token: str, classroom_id: int) -> list[AssignmentInfo]:
    """List all assignments in a GitHub Classroom."""
    results: list[AssignmentInfo] = []
    page = 1
    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            resp = await client.get(
                f"{CLASSROOM_API}/classrooms/{classroom_id}/assignments",
                headers={
                    "Authorization": f"Bearer {admin_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"per_page": 100, "page": page},
            )
            if resp.status_code != 200:
                logger.warning(
                    "Failed to list assignments for classroom %s: %s %s",
                    classroom_id,
                    resp.status_code,
                    resp.text,
                )
                break
            data = resp.json()
            if not data:
                break
            for a in data:
                cr = a.get("classroom", {})
                results.append(
                    AssignmentInfo(
                        id=a["id"],
                        title=a["title"],
                        slug=a["slug"],
                        invite_link=a.get("invite_link", ""),
                        classroom_id=classroom_id,
                        classroom_url=cr.get("url", ""),
                    )
                )
            if len(data) < 100:
                break
            page += 1
    return results
