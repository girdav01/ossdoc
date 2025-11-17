"""
Documentation Downloader - Downloads documentation from GitHub repositories
"""

import os
import re
import time
import requests
from typing import Dict, List, Optional
from pathlib import Path
import html2text
import markdown


class DocDownloader:
    """Downloads and processes documentation from GitHub repositories"""

    def __init__(self, config: dict, output_dir: str):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay = config.get('scraping', {}).get('delay_between_requests', 1)
        self.max_retries = config.get('scraping', {}).get('max_retries', 3)
        self.timeout = config.get('scraping', {}).get('timeout', 30)
        self.user_agent = config.get('scraping', {}).get('user_agent', 'Mozilla/5.0')

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_emphasis = False

    def fetch_file(self, url: str) -> Optional[str]:
        """Fetch file content from URL with retries"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                time.sleep(self.delay)
                return response.text
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"  Failed to fetch {url}: {e}")
                    return None
                time.sleep(self.delay * (attempt + 1))
        return None

    def get_repo_files(self, owner: str, repo: str) -> List[Dict]:
        """Get list of files from GitHub repository"""
        # Use GitHub API to get repository tree
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"

        # Try 'main' first, then 'master'
        for branch in ['main', 'master']:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            try:
                response = self.session.get(api_url, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    return data.get('tree', [])
            except:
                continue

        return []

    def download_readme(self, owner: str, repo: str) -> Optional[Dict[str, str]]:
        """Download README file from repository"""
        readme_names = ['README.md', 'readme.md', 'README.MD', 'Readme.md',
                        'README.rst', 'README.txt', 'README']

        for readme_name in readme_names:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{readme_name}"

            content = self.fetch_file(url)
            if content:
                return {
                    'filename': readme_name,
                    'content': content,
                    'type': 'readme'
                }

            # Try master branch
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{readme_name}"
            content = self.fetch_file(url)
            if content:
                return {
                    'filename': readme_name,
                    'content': content,
                    'type': 'readme'
                }

        return None

    def download_docs_folder(self, owner: str, repo: str) -> List[Dict[str, str]]:
        """Download documentation from docs/ folder"""
        docs = []
        files = self.get_repo_files(owner, repo)

        # Look for documentation files
        doc_patterns = [
            r'^docs?/.*\.(md|rst|txt)$',
            r'^documentation/.*\.(md|rst|txt)$',
            r'.*\.md$',  # Any markdown file
        ]

        for file_info in files:
            if file_info.get('type') != 'blob':
                continue

            path = file_info.get('path', '')

            # Check if it matches documentation patterns
            is_doc = any(re.match(pattern, path, re.IGNORECASE) for pattern in doc_patterns)

            if is_doc and not path.startswith('.'):
                # Download the file
                for branch in ['main', 'master']:
                    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
                    content = self.fetch_file(url)
                    if content:
                        docs.append({
                            'filename': path,
                            'content': content,
                            'type': 'documentation'
                        })
                        break

                # Limit documentation files per repo to avoid overwhelming
                if len(docs) >= 20:
                    break

        return docs

    def download_repo_docs(self, tool: Dict[str, str]) -> Dict[str, any]:
        """Download all documentation for a repository"""
        owner = tool['owner']
        repo = tool['name']
        github_url = tool['github_url']

        print(f"  Downloading docs for {owner}/{repo}")

        result = {
            'tool': tool,
            'readme': None,
            'docs': [],
            'metadata': {
                'owner': owner,
                'repo': repo,
                'github_url': github_url
            }
        }

        # Download README
        readme = self.download_readme(owner, repo)
        if readme:
            result['readme'] = readme
            print(f"    Downloaded README")

        # Download documentation files
        docs = self.download_docs_folder(owner, repo)
        result['docs'] = docs
        if docs:
            print(f"    Downloaded {len(docs)} documentation files")

        # Save to disk
        self.save_repo_docs(owner, repo, result)

        return result

    def save_repo_docs(self, owner: str, repo: str, docs_data: Dict):
        """Save downloaded documentation to disk"""
        repo_dir = self.output_dir / owner / repo
        repo_dir.mkdir(parents=True, exist_ok=True)

        # Save README
        if docs_data.get('readme'):
            readme = docs_data['readme']
            readme_path = repo_dir / readme['filename']
            readme_path.write_text(readme['content'], encoding='utf-8')

        # Save documentation files
        for doc in docs_data.get('docs', []):
            # Preserve directory structure
            doc_path = repo_dir / doc['filename']
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            doc_path.write_text(doc['content'], encoding='utf-8')

    def download_all_tools(self, tools: List[Dict[str, str]]) -> List[Dict]:
        """Download documentation for all tools"""
        all_docs = []

        for i, tool in enumerate(tools, 1):
            print(f"\n[{i}/{len(tools)}] Processing {tool['name']}")
            try:
                docs = self.download_repo_docs(tool)
                all_docs.append(docs)
            except Exception as e:
                print(f"  Error processing {tool['name']}: {e}")
                continue

        return all_docs
