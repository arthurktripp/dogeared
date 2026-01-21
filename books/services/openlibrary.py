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


# ############## #
# Replaced Logic #
# ############## #

def ol_search_basic_old(query: dict, limit: int = 10, offset: int = 0):
    # queries Open Library requesting basic works-level data.
    query['fields'] = FIELDS
    query['language'] = 'eng'
    query['offset'] = offset
    query['limit'] = limit

    r = requests.get(SEARCH_BASE_URL, params=query)
    data = r.json()

    # for development:
    print(r.url)
    print(r.text)

    return data


class OL_Edition:
    '''
    Represents an Open Library edition.
    Primarily used in scoring the edition as a candidate for affiliate links.

    :var Score: Description
    :var Format: Description
    :var Since: Description
    :var isbn_13: Description
    :var isbn_10: Description
    '''

    def __init__(self, isbn):
        query = {'fields': 'title,author_name,publish_date,physical_format,'}
        try:
            r = requests.get(f'{ISBN_BASE_URL}{isbn}.json', params=query)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as e:
            # ValueError covers JSON decode errors
            print(f"OpenLibrary error for ISBN {isbn}: {e}")
            data = {}

        self.physical_format = self.get_format(data)
        self.language = self.get_language(data)
        self.years_since = self.get_years_since(data)
        self.isbn_13 = data.get('isbn_13')
        self.isbn_10 = data.get('isbn_10')

        self.confidence_score = 0

    def __str__(self):
        return f'''
                Confidence Score: {self.confidence_score}
                Physical Format: {self.physical_format}
                Years Since: {self.years_since}
                isbn_13: {self.isbn_13}
                isbn_10: {self.isbn_10}
                '''

    def get_format(self, data):
        physical_format = data.get('physical_format')
        if physical_format:
            return physical_format.lower()
        return None

    def get_language(self, data):
        languages = data.get('languages')
        if languages:
            return languages[0]['key'].split('/')[2]
        return None

    def get_years_since(self, data):
        publish_date = data.get('publish_date')
        match = re.search(r"\b(18|19|20)\d{2}\b", str(publish_date))
        year = int(match.group()) if match else None

        years_since = date.today().year - year if year else None
        return years_since


def edition_scoring(search_results: dict):
    isbns = search_results['docs'][0]['isbn']

    query = {
        'fields': 'title,author_name,publish_date,physical_format,'
    }

    GOOD_FORMATS = [
        'hardcover',
        'paperback',
        'mass market paperback'
    ]
    BAD_FORMATS = [
        'audio cd',
        'audio cassette'
        'digital book',
        'electronic resource',
        'none',
        'school & library binding',
    ]

    top_result = None

    for isbn in isbns:
        edition = OL_Edition(isbn)

        if edition.physical_format in BAD_FORMATS:
            edition.confidence_score -= 10
        elif edition.physical_format in GOOD_FORMATS:
            edition.confidence_score += 10
        else:
            edition.confidence_score -= 5

        if not edition.language:
            edition.confidence_score -= 10
        elif edition.language == 'eng':
            edition.confidence_score += 10
        else:
            edition.confidence_score -= 20

        if not edition.years_since:
            edition.confidence_score -= 20
        else:
            edition.confidence_score -= (edition.years_since * .3)

        if not top_result:
            top_result = edition
            print(top_result)
            continue

        if edition.confidence_score > top_result.confidence_score:
            print(top_result)
            top_result = edition

    return top_result


if __name__ == '__main__':
    # Find a book, then get the optimal edition for linking out
    print('Search OpenLibrary: ')
    search_query = input()
    # payload = {"q": search_query}
    # search_results = ol_search_basic(payload)
    # print()
    # print(ol_search_basic2(q=search_query))

    # print(edition_scoring(search_results))
