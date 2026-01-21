from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import requests
from typing import Any

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


def gb_search_basic(*, q: str, limit: int = 10, offset: int = 0, language: str = 'en'):
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


# ############## #
# Replaced Logic #
# ############## #

class SearchResult:
    def __init__(self, item_data):
        self.volume_info = item_data.get('volumeInfo')
        self.google_id = item_data.get('id')

        self.title = self.volume_info.get('title')
        self.authors = self.volume_info.get('authors')
        self.published = self.volume_info.get('publishedDate')
        self.maturity_rating = self.volume_info.get('maturityRating')
        self.thumbnails = self.volume_info.get('imageLinks')
        self.google_url = self.get_google_v2_url()

    def __repr__(self):
        authors = ", ".join(self.authors) if self.authors else "Unknown"
        return f'''
                Title: {self.title}
                Author(s): {authors}
                Published: {self.published}
                Google Link: {self.google_url}
                '''

    def get_google_v2_url(self):
        return f'https://www.google.com/books/edition/_/{self.google_id}'


def gb_basic_search(search_terms: str, results_count=10, page=1):
    query = {
        'q': search_terms,
        'key': getenv('GOOGLE_BOOKS_API_KEY'),
        'maxResults': results_count,
        'startIndex': (page - 1) * results_count,
        'printType': 'books',
        # 'projection': 'lite',
        # 'orderBy': 'newest',
        'langRestrict': 'en'
    }
    try:
        r = requests.get(SEARCH_BASE_URL, params=query)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        # ValueError covers JSON decode errors
        print(f"Google Books API error for {query['q']}: {e}")
        data = {'items': []}

    results = []
    for item in data['items']:
        result = SearchResult(item)
        results.append(result)

    print(r.url)
    return results


# def process_search_results(search_results: dict):
#     results = []
#     for item in search_results['items']:
#         result = SearchResult(item)
#         results.append(result)

#     return results


if __name__ == '__main__':
    search_query = input('Search Google Books: ')
    # results = gb_basic_search(search_query)
    # processed_results = process_search_results(results)
    search_results = gb_search_basic(q=search_query)
    print(search_results.num_found, search_results.start)
    for result in search_results.results:
        print(result)
