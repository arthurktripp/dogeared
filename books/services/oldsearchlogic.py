from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import re
import requests

from dotenv import load_dotenv
from os import getenv

SEARCH_BASE_URL = ''
FIELDS = "key,title,subtitle,author_name,first_publish_year,cover_i,isbn"
ISBN_BASE_URL = 'https://openlibrary.org/isbn/'

# ############## #
# Replaced Google Search Logic
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





# ############## #
# Replaced Open Library Logic #
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


