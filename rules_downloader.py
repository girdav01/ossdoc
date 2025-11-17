"""
YARA and Sigma Rules Downloader
"""

import os
import re
import time
import requests
from typing import Dict, List, Optional
from pathlib import Path


class RulesDownloader:
    """Downloads YARA and Sigma rules from various sources"""

    def __init__(self, config: dict, output_dir: str):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay = config.get('scraping', {}).get('delay_between_requests', 1)
        self.max_retries = config.get('scraping', {}).get('max_retries', 3)
        self.timeout = config.get('scraping', {}).get('timeout', 30)

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'CybersecurityDocsBot/1.0'})

    def fetch_file(self, url: str) -> Optional[str]:
        """Fetch file content from URL"""
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

    def get_repo_files(self, owner: str, repo: str, branch: str = 'main') -> List[Dict]:
        """Get list of files from GitHub repository using API"""
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"

        for branch in ['main', 'master']:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            try:
                response = self.session.get(api_url, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    return data.get('tree', [])
                time.sleep(self.delay)
            except Exception as e:
                print(f"  Error fetching repo tree: {e}")
                continue

        return []

    def download_yara_rules(self) -> Dict[str, List]:
        """Download YARA rules from configured sources"""
        print("\n=== Downloading YARA Rules ===")

        yara_dir = self.output_dir / 'yara_rules'
        yara_dir.mkdir(parents=True, exist_ok=True)

        all_rules = []
        yara_sources = self.config.get('yara_sources', [])

        for source in yara_sources:
            url = source['url']
            name = source['name']

            print(f"\nDownloading from {name}")

            # Extract owner and repo from GitHub URL
            parts = url.replace('https://github.com/', '').split('/')
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]

                # Get all files
                files = self.get_repo_files(owner, repo)

                # Filter for YARA files
                yara_files = [f for f in files
                              if f.get('type') == 'blob' and
                              (f.get('path', '').endswith('.yar') or
                               f.get('path', '').endswith('.yara'))]

                print(f"  Found {len(yara_files)} YARA rule files")

                # Download YARA files (limit to prevent overwhelming)
                for i, file_info in enumerate(yara_files[:50]):  # Limit to 50 per source
                    path = file_info['path']

                    for branch in ['main', 'master']:
                        file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
                        content = self.fetch_file(file_url)

                        if content:
                            rule_data = {
                                'source': name,
                                'filename': path,
                                'content': content,
                                'url': file_url
                            }
                            all_rules.append(rule_data)

                            # Save to disk
                            rule_path = yara_dir / name / path
                            rule_path.parent.mkdir(parents=True, exist_ok=True)
                            rule_path.write_text(content, encoding='utf-8')

                            break

                    if (i + 1) % 10 == 0:
                        print(f"    Downloaded {i + 1}/{min(len(yara_files), 50)} rules")

        # Also download YARA documentation
        self.download_yara_documentation(yara_dir)

        print(f"\nTotal YARA rules downloaded: {len(all_rules)}")
        return {
            'rules': all_rules,
            'total': len(all_rules)
        }

    def download_yara_documentation(self, yara_dir: Path):
        """Download official YARA documentation"""
        print("\n  Downloading YARA official documentation...")

        # YARA official docs
        yara_docs = [
            {
                'name': 'YARA_Documentation.md',
                'url': 'https://raw.githubusercontent.com/VirusTotal/yara/master/README.md'
            },
            {
                'name': 'Writing_Rules.md',
                'url': 'https://yara.readthedocs.io/en/stable/writingrules.html'
            }
        ]

        docs_dir = yara_dir / 'official_docs'
        docs_dir.mkdir(parents=True, exist_ok=True)

        for doc in yara_docs:
            content = self.fetch_file(doc['url'])
            if content:
                doc_path = docs_dir / doc['name']
                doc_path.write_text(content, encoding='utf-8')
                print(f"    Downloaded {doc['name']}")

    def download_sigma_rules(self) -> Dict[str, List]:
        """Download Sigma rules from configured sources"""
        print("\n=== Downloading Sigma Rules ===")

        sigma_dir = self.output_dir / 'sigma_rules'
        sigma_dir.mkdir(parents=True, exist_ok=True)

        all_rules = []
        sigma_sources = self.config.get('sigma_sources', [])

        for source in sigma_sources:
            url = source['url']
            name = source['name']

            print(f"\nDownloading from {name}")

            # Extract owner and repo from GitHub URL
            parts = url.replace('https://github.com/', '').split('/')
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]

                # Get all files
                files = self.get_repo_files(owner, repo)

                # Filter for Sigma files (YAML files in rules directory)
                sigma_files = [f for f in files
                               if f.get('type') == 'blob' and
                               f.get('path', '').endswith('.yml') and
                               ('rules/' in f.get('path', '') or 'rules-' in f.get('path', ''))]

                print(f"  Found {len(sigma_files)} Sigma rule files")

                # Download Sigma files (limit to prevent overwhelming)
                for i, file_info in enumerate(sigma_files[:100]):  # Limit to 100 per source
                    path = file_info['path']

                    for branch in ['main', 'master']:
                        file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
                        content = self.fetch_file(file_url)

                        if content:
                            rule_data = {
                                'source': name,
                                'filename': path,
                                'content': content,
                                'url': file_url
                            }
                            all_rules.append(rule_data)

                            # Save to disk
                            rule_path = sigma_dir / name / path
                            rule_path.parent.mkdir(parents=True, exist_ok=True)
                            rule_path.write_text(content, encoding='utf-8')

                            break

                    if (i + 1) % 20 == 0:
                        print(f"    Downloaded {i + 1}/{min(len(sigma_files), 100)} rules")

        # Also download Sigma documentation
        self.download_sigma_documentation(sigma_dir)

        print(f"\nTotal Sigma rules downloaded: {len(all_rules)}")
        return {
            'rules': all_rules,
            'total': len(all_rules)
        }

    def download_sigma_documentation(self, sigma_dir: Path):
        """Download official Sigma documentation"""
        print("\n  Downloading Sigma official documentation...")

        # Sigma official docs
        sigma_docs = [
            {
                'name': 'Sigma_README.md',
                'url': 'https://raw.githubusercontent.com/SigmaHQ/sigma/master/README.md'
            },
            {
                'name': 'Sigma_Specification.md',
                'url': 'https://raw.githubusercontent.com/SigmaHQ/sigma-specification/main/Sigma_specification.md'
            }
        ]

        docs_dir = sigma_dir / 'official_docs'
        docs_dir.mkdir(parents=True, exist_ok=True)

        for doc in sigma_docs:
            content = self.fetch_file(doc['url'])
            if content:
                doc_path = docs_dir / doc['name']
                doc_path.write_text(content, encoding='utf-8')
                print(f"    Downloaded {doc['name']}")

    def download_all_rules(self) -> Dict:
        """Download both YARA and Sigma rules"""
        yara_result = self.download_yara_rules()
        sigma_result = self.download_sigma_rules()

        return {
            'yara': yara_result,
            'sigma': sigma_result,
            'total_rules': yara_result['total'] + sigma_result['total']
        }
