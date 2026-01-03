from datetime import date
import requests
import re


SEARCH_BASE_URL = 'https://openlibrary.org/search.json'
ISBN_BASE_URL = 'https://openlibrary.org/isbn/'


def ol_search_basic(query: dict, limit: int, offset: int):
    query['fields'] = 'title,subtitle,author_name,first_publish_year,key,isbn'
    query['language'] = 'eng'
    query['offset'] = offset
    query['limit'] = limit
    r = requests.get(SEARCH_BASE_URL, params=query)
    data = r.json()
    print(r.url)
    print(r.text)
    return data


class OL_Edition:
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
    payload = {"q": search_query}
    search_results = ol_search_basic(payload, 1, 0)

    print(edition_scoring(search_results))
