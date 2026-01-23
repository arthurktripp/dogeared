from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import re
import requests

SEARCH_BASE_URL = 'https://openlibrary.org/search.json'
COVERS_BASE_URL = "https://covers.openlibrary.org/b/id"
ISBN_BASE_URL = 'https://openlibrary.org/isbn/'

FIELDS = "key,title,subtitle,author_name,first_publish_year,cover_i,isbn"


@dataclass(frozen=True)
class OLWorkSearchResult:
    work_key: str
    title: str
    subtitle: str | None
    authors: list[str]
    first_publish_year: int | None
    cover_url: str | None
    isbns: list[str]


@dataclass(frozen=True)
class OLSearchResponse:
    num_found: int
    start: int
    results: list[OLWorkSearchResult]


def _cover_url(cover_i: int | None, size: str = "M") -> str | None:
    # size: S, M, L
    if not cover_i:
        return None
    return f"{COVERS_BASE_URL}/{cover_i}-{size}.jpg"


def _as_list(value: Any) -> list:
    # OL sometimes omits keys; also keeps typing sane.
    return value if isinstance(value, list) else []


def map_doc_to_result(doc: dict[str, Any]) -> OLWorkSearchResult:
    title = (doc.get("title") or "").strip()
    subtitle = (doc.get("subtitle") or None)
    subtitle = subtitle.strip() if isinstance(
        subtitle, str) and subtitle.strip() else None

    authors = [a.strip() for a in _as_list(doc.get("author_name"))
               if isinstance(a, str) and a.strip()]
    isbns = [i.strip() for i in _as_list(doc.get("isbn"))
             if isinstance(i, str) and i.strip()]

    # key is typically like "/works/OL...W"
    work_key = doc.get("key") or ""
    if not work_key.startswith("/works/"):
        # keep it predictable; you can also choose to raise here
        work_key = f"/works/{work_key}" if work_key else ""

    year = doc.get("first_publish_year")
    year = year if isinstance(year, int) else None

    cover_i = doc.get("cover_i")
    cover_i = cover_i if isinstance(cover_i, int) else None

    return OLWorkSearchResult(
        work_key=work_key,
        title=title or "(Untitled)",
        subtitle=subtitle,
        authors=authors,
        first_publish_year=year,
        cover_url=_cover_url(cover_i, size="M"),
        isbns=isbns,
    )


def ol_search_basic(*, q: str, limit: int = 10, offset: int = 0, language: str = "eng") -> OLSearchResponse:
    params = {
        "q": q,
        "fields": FIELDS,
        "language": language,
        "limit": limit,
        "offset": offset,
    }

    r = requests.get(SEARCH_BASE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    docs = data.get("docs") or []
    results = [map_doc_to_result(doc) for doc in docs if isinstance(doc, dict)]

    return OLSearchResponse(
        num_found=int(data.get("numFound") or 0),
        start=int(data.get("start") or 0),
        results=results,
    )



if __name__ == '__main__':
    # Find a book, then get the optimal edition for linking out
    print('Search OpenLibrary: ')
    search_query = input()