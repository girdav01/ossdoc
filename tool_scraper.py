"""
Tool List Scraper - Extracts cybersecurity tools from GitHub awesome lists
"""

import re
import requests
from typing import List, Dict, Set
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup


class ToolScraper:
    """Scrapes and extracts cybersecurity tools from various sources"""

    def __init__(self, config: dict):
        self.config = config
        self.delay = config.get('scraping', {}).get('delay_between_requests', 1)
        self.max_retries = config.get('scraping', {}).get('max_retries', 3)
        self.timeout = config.get('scraping', {}).get('timeout', 30)
        self.user_agent = config.get('scraping', {}).get('user_agent', 'Mozilla/5.0')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

    def fetch_content(self, url: str) -> str:
        """Fetch content from URL with retries"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                time.sleep(self.delay)
                return response.text
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"Failed to fetch {url}: {e}")
                    return ""
                time.sleep(self.delay * (attempt + 1))
        return ""

    def extract_github_urls(self, markdown_content: str) -> Set[str]:
        """Extract GitHub repository URLs from markdown content"""
        github_urls = set()

        # Pattern for markdown links
        md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(md_link_pattern, markdown_content)

        for text, url in matches:
            if 'github.com' in url:
                # Clean up the URL
                cleaned_url = self._clean_github_url(url)
                if cleaned_url:
                    github_urls.add(cleaned_url)

        # Also look for plain GitHub URLs
        url_pattern = r'https?://github\.com/[\w\-]+/[\w\-.]+'
        plain_urls = re.findall(url_pattern, markdown_content)
        for url in plain_urls:
            cleaned_url = self._clean_github_url(url)
            if cleaned_url:
                github_urls.add(cleaned_url)

        return github_urls

    def _clean_github_url(self, url: str) -> str:
        """Clean and normalize GitHub URL"""
        try:
            # Remove fragments and query parameters
            url = url.split('#')[0].split('?')[0]

            # Parse URL
            parsed = urlparse(url)
            if 'github.com' not in parsed.netloc:
                return ""

            # Extract owner and repo
            path_parts = [p for p in parsed.path.split('/') if p]
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                return f"https://github.com/{owner}/{repo}"

            return ""
        except:
            return ""

    def scrape_awesome_list(self, url: str, name: str) -> List[Dict[str, str]]:
        """Scrape an awesome list and extract tool information"""
        print(f"Scraping {name} from {url}")

        content = self.fetch_content(url)
        if not content:
            return []

        github_urls = self.extract_github_urls(content)

        tools = []
        for github_url in github_urls:
            path_parts = github_url.replace('https://github.com/', '').split('/')
            if len(path_parts) >= 2:
                tools.append({
                    'name': path_parts[1],
                    'owner': path_parts[0],
                    'github_url': github_url,
                    'source_list': name
                })

        print(f"Found {len(tools)} tools from {name}")
        return tools

    def scrape_all_sources(self, max_per_source: int = None) -> List[Dict[str, str]]:
        """Scrape all configured tool sources"""
        all_tools = []
        seen_urls = set()

        tool_sources = self.config.get('tool_sources', [])

        for source in tool_sources:
            url = source.get('url')
            name = source.get('name')
            source_type = source.get('type')

            if source_type == 'awesome_list':
                tools = self.scrape_awesome_list(url, name)

                # Deduplicate and limit
                for tool in tools:
                    if tool['github_url'] not in seen_urls:
                        seen_urls.add(tool['github_url'])
                        all_tools.append(tool)

                        if max_per_source and len(all_tools) >= max_per_source:
                            break

        print(f"\nTotal unique tools found: {len(all_tools)}")
        return all_tools
