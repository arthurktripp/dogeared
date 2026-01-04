from datetime import date
import requests
import re

from dotenv import load_dotenv
from os import getenv


load_dotenv()

SEARCH_BASE_URL = 'https://www.googleapis.com/books/v1/volumes'

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
                Google Link: {self.google_url}\n
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
        
    return results


# def process_search_results(search_results: dict):
#     results = []
#     for item in search_results['items']:
#         result = SearchResult(item)
#         results.append(result)
        
#     return results





if __name__ == '__main__':
    search_query = input('Search Google Books: ')
    results = gb_basic_search(search_query)
    # processed_results = process_search_results(results)
    print(results)
    