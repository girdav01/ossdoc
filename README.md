# Cybersecurity Documentation Scraper & Dataset Creator

A comprehensive tool for scraping cybersecurity OSS tool documentation and creating instruction datasets for LLM fine-tuning. This project automatically discovers top cybersecurity tools from curated GitHub awesome lists, downloads their documentation, collects YARA and Sigma rules, and formats everything into an instruction dataset suitable for training large language models.

## Features

- **Automated Tool Discovery**: Scrapes multiple "awesome" lists to find top cybersecurity tools
- **Documentation Downloading**: Downloads README files and documentation from GitHub repositories
- **YARA Rules Collection**: Fetches YARA rules from major repositories and includes official documentation
- **Sigma Rules Collection**: Downloads Sigma detection rules with official specifications
- **Instruction Dataset Generation**: Converts all documentation into instruction-response pairs for LLM fine-tuning
- **Comprehensive Coverage**: Covers tools across multiple security domains (pentesting, incident response, threat intelligence, etc.)

## Architecture

The project consists of several modules:

- `tool_scraper.py`: Extracts cybersecurity tool lists from GitHub awesome lists
- `doc_downloader.py`: Downloads documentation from GitHub repositories
- `rules_downloader.py`: Downloads YARA and Sigma rules from official sources
- `dataset_formatter.py`: Creates instruction datasets in JSONL format
- `main.py`: Orchestrates the entire pipeline
- `config.yaml`: Configuration for sources and scraping parameters

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

Run the main script to execute the entire pipeline:

```bash
python main.py
```

The script will:
1. Scrape tool lists from configured awesome lists
2. Download documentation from each tool's GitHub repository
3. Download YARA and Sigma rules from official repositories
4. Create an instruction dataset in JSONL format

## Output Structure

```
ossdoc/
├── docs/                           # Downloaded documentation
│   ├── yara_rules/                # YARA rules and documentation
│   ├── sigma_rules/               # Sigma rules and documentation
│   └── [owner]/[repo]/            # Tool documentation by repository
├── datasets/                      # Generated datasets
│   ├── cybersecurity_instruct_dataset.jsonl
│   └── dataset_summary.json
├── tools_list.json               # List of discovered tools
├── docs_metadata.json            # Documentation metadata
└── rules_metadata.json           # Rules metadata
```

## Dataset Format

The instruction dataset is in JSONL format, with each line containing:

```json
{
  "instruction": "What is Metasploit?",
  "input": "",
  "output": "Metasploit is a penetration testing framework...",
  "metadata": {
    "tool": "metasploit-framework",
    "category": "cybersecurity",
    "source": "https://github.com/rapid7/metasploit-framework",
    "type": "tool_description"
  }
}
```

## Instruction Types

The dataset includes various instruction types:

- **Tool descriptions**: Overview of what each tool does
- **Installation guides**: How to install and set up tools
- **Usage examples**: How to use the tools
- **Feature explanations**: Detailed feature descriptions
- **YARA rule explanations**: Understanding malware detection rules
- **Sigma rule explanations**: Understanding threat detection rules

## Configuration

Edit `config.yaml` to customize:

- Tool sources (awesome lists)
- YARA and Sigma rule repositories
- Output directories
- Scraping parameters (delays, timeouts, etc.)
- Maximum tools per source

## Sources

### Tool Lists
- awesome-security
- awesome-hacking
- awesome-threat-intelligence
- awesome-incident-response

### YARA Rules
- Yara-Rules/rules
- elastic/protections-artifacts
- reversinglabs/reversinglabs-yara-rules

### Sigma Rules
- SigmaHQ/sigma

## Use Cases

This dataset can be used for:

- Fine-tuning LLMs on cybersecurity knowledge
- Training AI assistants for security operations
- Creating chatbots for security tool guidance
- Building knowledge bases for SOC analysts
- Educational purposes in cybersecurity training

## License

This tool is for educational and research purposes. Please respect the licenses of the scraped repositories and use the data ethically.

## Notes

- The scraper includes delays between requests to be respectful to GitHub
- Rate limiting may occur with extensive scraping
- Some repositories may require authentication for API access
- The dataset size depends on configured limits and available documentation
