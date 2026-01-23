from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import requests
from typing import Any, Optional

from dotenv import load_dotenv
from os import getenv

SEARCH_BASE_URL = 'https://www.googleapis.com/books/v1/volumes'
load_dotenv()


@dataclass(frozen=True)
class GBSearchResult:
    google_id: str
    google_url: str | None
    title: str
    subtitle: str | None
    authors: list[str]
    text_snippet: str | None
    cover_url: str | None


@dataclass(frozen=True)
class GBSearchResponse:
    num_found: int
    start: int
    results: list[GBSearchResult]


@dataclass(frozen=True)
class SearchParams:
    q: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None


def build_google_q(p: SearchParams) -> str:
    parts: list[str] = []


    # free text (keep it last so it broadens rather than overrides)
    if p.q:
        parts.append(p.q.strip())
        
    # structured fields
    if p.title:
        parts.append(f'intitle:"{p.title.strip()}"')
    if p.author:
        parts.append(f'inauthor:"{p.author.strip()}"')

    # free text (keep it last so it broadens rather than overrides)
    if p.q:
        parts.append(p.q.strip())

    # If user submitted an empty advanced form, avoid q=""
    return " ".join(parts).strip()


def _google_url(google_id: str):
    if google_id is not ('' or None):
        return f'https://www.google.com/books/edition/_/{google_id}'
    return None


def map_item_to_result(item: dict[str, Any]) -> GBSearchResult:
    volume_info = item.get('volumeInfo')
    image_links = volume_info.get('imageLinks')
    search_info = item.get('searchInfo')

    google_id = (item.get('id') or '').strip()
    google_url = _google_url(google_id)

    title = (volume_info.get('title'))
    subtitle = (volume_info.get('subtitle')) or ''
    authors = (volume_info.get('authors')) or []
    cover_url = image_links.get('thumbnail') if image_links else ''
    text_snippet = search_info.get('textSnippet') if search_info else ''

    return GBSearchResult(
        google_id=google_id,
        google_url=google_url,
        title=title or "(Untitled)",
        subtitle=subtitle,
        authors=authors,
        cover_url=cover_url,
        text_snippet=text_snippet,
    )


def gb_search(*, limit: int = 10, offset: int = 0, language: str = 'en', **kwargs):
    search_parameters = SearchParams(**kwargs)
    q = build_google_q(search_parameters)
    if not q:
        return GBSearchResponse(
            num_found=0,
            start=0,
            results=[]
        )
    params = {
        'q': q,
        'maxResults': limit,
        'startIndex': offset,
        'langRestrict': language,
        'key': getenv('GOOGLE_BOOKS_API_KEY')
    }

    try:
        r = requests.get(SEARCH_BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        # ValueError covers JSON decode errors
        # print(f"Google Books API error for {params['q']}: {e}")
        data = {'items': []}

    items = data.get("items") or []
    results = [map_item_to_result(item)
               for item in items if isinstance(item, dict)]

    return GBSearchResponse(
        num_found=int(data.get('totalItems') or 0),
        start=offset,
        results=results,
    )




if __name__ == '__main__':
    search_query = input('Search Google Books: ')
    print(gb_search(text=search_query))
