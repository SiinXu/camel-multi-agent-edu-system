import requests
from bs4 import BeautifulSoup

class WebScraperTool:
    """网页抓取工具."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def scrape(self, url: str) -> str:
        """抓取指定 URL 的网页内容."""
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.get_text()
        except requests.exceptions.RequestException as e:
            return f"An error occurred: {e}"

    def __call__(self, url: str) -> str:
        """使实例可调用."""
        return self.scrape(url)