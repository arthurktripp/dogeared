from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import html, requests
from typing import Any, Optional

from dotenv import load_dotenv
from os import getenv

from books.models import Book

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
    if p.q:
        parts.append(p.q.strip())
        
    if p.title:
        parts.append(f'intitle:"{p.title.strip()}"')
    if p.author:
        parts.append(f'inauthor:"{p.author.strip()}"')

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
    text_snippet = html.unescape(search_info.get('textSnippet') if search_info else '')


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
        print(f"Google Books API error for {params['q']}: {e}")
        data = {'items': []}

    items = data.get("items") or []
    results = [map_item_to_result(item)
               for item in items if isinstance(item, dict)]

    return GBSearchResponse(
        num_found=int(data.get('totalItems') or 0),
        start=offset,
        results=results,
    )


@dataclass(frozen=True)
class BookDetail:
    google_id: str
    title: str
    subtitle: str | None
    authors: list[str]
    description: str | None
    main_category: str | None
    categories: list[str] | None
    language: str | None
    avg_rating: int | None
    image_links: dict[str, Any] | None
    # is_mature: bool
    identifiers: dict | None
    

def map_to_detail(item: dict[str, Any]) -> BookDetail:
    google_id = item.get('id')
    volume_info = item.get('volumeInfo')
    
    title = volume_info.get('title')
    subtitle = volume_info.get('subtitle')
    authors = volume_info.get('authors')
    
    description = volume_info.get('description')
    if description:
        description = html.unescape(description)
    
    main_category = volume_info.get('mainCategory')
    categories = volume_info.get('categories')
    language = volume_info.get('langiage')
    avg_rating = volume_info.get('averageRating')
    # is_mature = volume_info.get('maturityRating') == 'MATURE'
    
    image_links = volume_info.get('imageLinks')
    
    industry_identifiers = volume_info.get('industryIdentifiers')
    if industry_identifiers:
        identifiers = {
            item["type"]: item["identifier"]
            for item in industry_identifiers
            }
    else:
        identifiers = {}
        
    detail = BookDetail(
        google_id=google_id,
        title=title,
        subtitle=subtitle,
        authors=authors,
        description=description,
        main_category=main_category,
        categories=categories,
        language=language,
        avg_rating=avg_rating,
        image_links=image_links,
        # is_mature=is_mature,
        identifiers=identifiers,
    )
    return detail


def retrieve_volume(volume_id: str) -> object | None:
    try:
        params = {'key': getenv('GOOGLE_BOOKS_API_KEY')}
        r = requests.get(f'{SEARCH_BASE_URL}/{volume_id}', params)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        print(f"Google Books API error for {volume_id}: {e}")
        return None
    return map_to_detail(data)
        


if __name__ == '__main__':
    # search_query = input('Search Google Books: ')
    # print(gb_search(text=search_query))
    
    volume_id = input('Enter a Google Volume ID:')
    print(retrieve_volume(volume_id))



def create_book_object(book_attrs: object) -> Book:

    book, created = Book.objects.get_or_create(
        source=book_attrs["source"],
        external_id=book_attrs["external_id"],
        title=book_attrs["title"],
        authors=book_attrs["authors"]
    )

    return book
