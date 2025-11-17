#!/usr/bin/env python3
"""
Cybersecurity Documentation Scraper and Dataset Creator
Main execution script
"""

import os
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime

from tool_scraper import ToolScraper
from doc_downloader import DocDownloader
from rules_downloader import RulesDownloader
from dataset_formatter import DatasetFormatter


def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def save_progress(data: dict, filename: str):
    """Save progress to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Main execution function"""
    print("=" * 80)
    print("Cybersecurity Documentation Scraper and Dataset Creator")
    print("=" * 80)

    # Load configuration
    print("\nLoading configuration...")
    config = load_config('config.yaml')

    # Create output directories
    output_config = config.get('output', {})
    docs_dir = output_config.get('docs_dir', 'docs')
    dataset_dir = output_config.get('dataset_dir', 'datasets')

    Path(docs_dir).mkdir(parents=True, exist_ok=True)
    Path(dataset_dir).mkdir(parents=True, exist_ok=True)

    print(f"  Documentation directory: {docs_dir}")
    print(f"  Dataset directory: {dataset_dir}")

    # Initialize components
    tool_scraper = ToolScraper(config)
    doc_downloader = DocDownloader(config, docs_dir)
    rules_downloader = RulesDownloader(config, docs_dir)
    dataset_formatter = DatasetFormatter(dataset_dir)

    # Step 1: Scrape tool lists
    print("\n" + "=" * 80)
    print("STEP 1: Scraping Cybersecurity Tool Lists")
    print("=" * 80)

    max_tools = config.get('output', {}).get('max_tools_per_source')
    tools = tool_scraper.scrape_all_sources(max_per_source=max_tools)

    # Save tool list
    tools_file = Path('tools_list.json')
    save_progress({'tools': tools, 'count': len(tools)}, str(tools_file))
    print(f"\nSaved tool list to: {tools_file}")

    # Step 2: Download documentation
    print("\n" + "=" * 80)
    print("STEP 2: Downloading Documentation from GitHub")
    print("=" * 80)

    tools_docs = doc_downloader.download_all_tools(tools)

    # Save documentation metadata
    docs_metadata_file = Path('docs_metadata.json')
    save_progress({
        'tools_count': len(tools_docs),
        'timestamp': datetime.now().isoformat()
    }, str(docs_metadata_file))

    # Step 3: Download YARA and Sigma rules
    print("\n" + "=" * 80)
    print("STEP 3: Downloading YARA and Sigma Rules")
    print("=" * 80)

    rules_data = rules_downloader.download_all_rules()

    # Save rules metadata
    rules_metadata_file = Path('rules_metadata.json')
    save_progress(rules_data, str(rules_metadata_file))

    # Step 4: Create instruction dataset
    print("\n" + "=" * 80)
    print("STEP 4: Creating Instruction Dataset for LLM Fine-tuning")
    print("=" * 80)

    dataset_file = dataset_formatter.format_all_to_dataset(tools_docs, rules_data)

    # Final summary
    print("\n" + "=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80)

    print(f"\nTools scraped: {len(tools)}")
    print(f"Documentation downloaded: {len(tools_docs)} repositories")
    print(f"YARA rules: {rules_data['yara']['total']}")
    print(f"Sigma rules: {rules_data['sigma']['total']}")
    print(f"Dataset file: {dataset_file}")

    print("\nAll files have been saved to the current directory.")
    print("Documentation files are in:", docs_dir)
    print("Dataset files are in:", dataset_dir)

    print("\n" + "=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
