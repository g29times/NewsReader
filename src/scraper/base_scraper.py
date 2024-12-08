import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScraper(ABC):
    """
    Abstract base class for web scrapers
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def fetch_page(self, url: str) -> BeautifulSoup:
        """
        Fetch and parse a webpage
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    @abstractmethod
    def extract_articles(self) -> List[Dict]:
        """
        Abstract method to extract articles from a source
        Must be implemented by child classes
        """
        pass

    @abstractmethod
    def validate_article(self, article: Dict) -> bool:
        """
        Validate extracted article data
        """
        pass
