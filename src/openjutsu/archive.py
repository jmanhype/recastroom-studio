# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


ARCHIVE_SEARCH_URL = "https://archive.org/advancedsearch.php"
ARCHIVE_DETAILS_URL = "https://archive.org/details/{identifier}"

VIDEO_COLLECTIONS = frozenset(
    {
        "prelinger",
        "moviesandfilms",
        "feature_films",
        "animationandcartoons",
    }
)


@dataclass(frozen=True)
class ArchiveSource:
    identifier: str
    title: str
    collection: str
    year: int | None = None
    downloads: int | None = None
    license_url: str | None = None

    def as_dict(self) -> dict[str, Any]:
        license_url = self.license_url or ""
        public_domain = "publicdomain" in license_url.lower()
        return {
            "identifier": self.identifier,
            "title": self.title,
            "collection": self.collection,
            "year": self.year,
            "downloads": self.downloads,
            "license_url": self.license_url,
            "details_url": ARCHIVE_DETAILS_URL.format(identifier=self.identifier),
            "rights": {
                "evidence": "explicit-archive-license" if license_url else "archive-license-url-missing",
                "public_domain": public_domain,
                "review_required": not public_domain,
            },
        }


class ArchiveSearchError(RuntimeError):
    """Archive.org discovery failed; no unverified result is returned."""


def search_public_video_sources(
    query: str,
    *,
    collection: str = "prelinger",
    limit: int = 12,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Search an allowlisted Archive.org video collection.

    The API needs no key. Results are discovery evidence only: an item without
    an explicit public-domain license remains rights-review-required.
    """
    collection = collection.strip().lower()
    if collection not in VIDEO_COLLECTIONS:
        raise ValueError("Unsupported Archive.org collection")
    if not 1 <= limit <= 24:
        raise ValueError("Limit must be between 1 and 24")

    text = " ".join(query.split())
    if not text or len(text) > 160:
        raise ValueError("Query must contain 1-160 characters")

    params: dict[str, Any] = {
        "q": f'collection:{collection} AND mediatype:movies AND ({text})',
        "rows": limit,
        "page": 1,
        "output": "json",
    }
    fields = ("identifier", "title", "year", "downloads", "licenseurl")
    params["fl[]"] = fields

    http = session or requests
    try:
        response = http.get(ARCHIVE_SEARCH_URL, params=params, timeout=12)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as error:
        raise ArchiveSearchError("Archive.org source discovery is unavailable") from error

    docs = payload.get("response", {}).get("docs", [])
    if not isinstance(docs, list):
        raise ArchiveSearchError("Archive.org returned an invalid search response")

    sources: list[dict[str, Any]] = []
    for item in docs:
        if not isinstance(item, dict) or not isinstance(item.get("identifier"), str):
            continue
        sources.append(
            ArchiveSource(
                identifier=item["identifier"],
                title=str(item.get("title") or item["identifier"]),
                collection=collection,
                year=_optional_int(item.get("year")),
                downloads=_optional_int(item.get("downloads")),
                license_url=_optional_str(item.get("licenseurl")),
            ).as_dict()
        )

    return {
        "provider": "archive.org",
        "api": "advancedsearch",
        "key_required": False,
        "collection": collection,
        "query": text,
        "result_count": len(sources),
        "sources": sources,
        "rights_notice": (
            "Archive metadata is discovery evidence. Import only after checking the item page and recording rights permission."
        ),
    }


def _optional_int(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
