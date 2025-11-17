"""
Dataset Formatter - Creates instruction datasets for LLM fine-tuning
"""

import json
import re
from typing import List, Dict
from pathlib import Path
from datetime import datetime


class DatasetFormatter:
    """Formats documentation into instruction datasets for LLM fine-tuning"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_instruction_from_readme(self, tool_data: Dict) -> List[Dict]:
        """Create instruction-response pairs from README content"""
        instructions = []

        tool = tool_data.get('tool', {})
        readme = tool_data.get('readme')
        metadata = tool_data.get('metadata', {})

        if not readme:
            return instructions

        tool_name = tool.get('name', 'Unknown')
        content = readme.get('content', '')

        # Create various instruction types

        # 1. General description
        instructions.append({
            'instruction': f"What is {tool_name}?",
            'input': '',
            'output': self._extract_description(content, tool_name),
            'metadata': {
                'tool': tool_name,
                'category': 'cybersecurity',
                'source': metadata.get('github_url', ''),
                'type': 'tool_description'
            }
        })

        # 2. Installation instructions
        install_section = self._extract_section(content, ['installation', 'install', 'setup', 'getting started'])
        if install_section:
            instructions.append({
                'instruction': f"How do I install {tool_name}?",
                'input': '',
                'output': install_section,
                'metadata': {
                    'tool': tool_name,
                    'category': 'cybersecurity',
                    'source': metadata.get('github_url', ''),
                    'type': 'installation'
                }
            })

        # 3. Usage instructions
        usage_section = self._extract_section(content, ['usage', 'how to use', 'examples', 'quickstart'])
        if usage_section:
            instructions.append({
                'instruction': f"How do I use {tool_name}?",
                'input': '',
                'output': usage_section,
                'metadata': {
                    'tool': tool_name,
                    'category': 'cybersecurity',
                    'source': metadata.get('github_url', ''),
                    'type': 'usage'
                }
            })

        # 4. Features
        features_section = self._extract_section(content, ['features', 'capabilities', 'what it does'])
        if features_section:
            instructions.append({
                'instruction': f"What are the main features of {tool_name}?",
                'input': '',
                'output': features_section,
                'metadata': {
                    'tool': tool_name,
                    'category': 'cybersecurity',
                    'source': metadata.get('github_url', ''),
                    'type': 'features'
                }
            })

        return instructions

    def create_instruction_from_doc(self, tool_name: str, doc: Dict, metadata: Dict) -> List[Dict]:
        """Create instruction-response pairs from documentation files"""
        instructions = []

        filename = doc.get('filename', '')
        content = doc.get('content', '')

        # Extract title from filename or content
        title = self._extract_title(filename, content)

        # Create Q&A pair
        instructions.append({
            'instruction': f"Explain {title} in {tool_name}",
            'input': '',
            'output': content[:4000],  # Limit length
            'metadata': {
                'tool': tool_name,
                'category': 'cybersecurity',
                'source': metadata.get('github_url', ''),
                'filename': filename,
                'type': 'documentation'
            }
        })

        return instructions

    def create_yara_instructions(self, rule_data: Dict) -> List[Dict]:
        """Create instruction-response pairs for YARA rules"""
        instructions = []

        filename = rule_data.get('filename', '')
        content = rule_data.get('content', '')
        source = rule_data.get('source', '')

        # Extract rule name
        rule_match = re.search(r'rule\s+(\w+)', content)
        rule_name = rule_match.group(1) if rule_match else 'Unknown'

        # General YARA rule explanation
        instructions.append({
            'instruction': f"Explain this YARA rule: {rule_name}",
            'input': content,
            'output': self._explain_yara_rule(content, rule_name),
            'metadata': {
                'category': 'yara',
                'source': source,
                'filename': filename,
                'type': 'rule_explanation'
            }
        })

        # Rule creation example
        instructions.append({
            'instruction': "Show me an example YARA rule for malware detection",
            'input': f"Category: {self._extract_yara_category(filename)}",
            'output': content[:2000],
            'metadata': {
                'category': 'yara',
                'source': source,
                'filename': filename,
                'type': 'rule_example'
            }
        })

        return instructions

    def create_sigma_instructions(self, rule_data: Dict) -> List[Dict]:
        """Create instruction-response pairs for Sigma rules"""
        instructions = []

        filename = rule_data.get('filename', '')
        content = rule_data.get('content', '')
        source = rule_data.get('source', '')

        # Extract title from YAML
        title_match = re.search(r'title:\s*(.+)', content)
        title = title_match.group(1).strip() if title_match else 'Unknown'

        # General Sigma rule explanation
        instructions.append({
            'instruction': f"Explain this Sigma rule: {title}",
            'input': content,
            'output': self._explain_sigma_rule(content, title),
            'metadata': {
                'category': 'sigma',
                'source': source,
                'filename': filename,
                'type': 'rule_explanation'
            }
        })

        # Rule creation example
        instructions.append({
            'instruction': "Show me an example Sigma rule for threat detection",
            'input': f"Detection type: {self._extract_sigma_category(filename)}",
            'output': content[:2000],
            'metadata': {
                'category': 'sigma',
                'source': source,
                'filename': filename,
                'type': 'rule_example'
            }
        })

        return instructions

    def _extract_description(self, content: str, tool_name: str) -> str:
        """Extract tool description from content"""
        lines = content.split('\n')

        # Look for first meaningful paragraph
        description = []
        in_description = False

        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()

            # Skip title
            if line.startswith('#'):
                in_description = True
                continue

            if in_description and line and not line.startswith('[') and not line.startswith('!'):
                description.append(line)

                # Stop after first paragraph
                if len(description) > 3:
                    break

        return ' '.join(description) if description else f"{tool_name} is a cybersecurity tool."

    def _extract_section(self, content: str, section_names: List[str]) -> str:
        """Extract a specific section from markdown content"""
        lines = content.split('\n')

        in_section = False
        section_content = []

        for i, line in enumerate(lines):
            # Check if this is a section header
            if line.startswith('#'):
                header_text = re.sub(r'^#+\s*', '', line).lower()

                # Check if it matches our section names
                if any(name in header_text for name in section_names):
                    in_section = True
                    continue
                elif in_section:
                    # Hit another section, stop
                    break

            if in_section and line.strip():
                section_content.append(line)

        result = '\n'.join(section_content).strip()
        return result[:3000] if result else ""  # Limit length

    def _extract_title(self, filename: str, content: str) -> str:
        """Extract title from filename or content"""
        # Try to get from first header in content
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Fall back to filename
        return Path(filename).stem.replace('_', ' ').replace('-', ' ').title()

    def _explain_yara_rule(self, content: str, rule_name: str) -> str:
        """Generate explanation for YARA rule"""
        explanation = f"This YARA rule named '{rule_name}' is designed for malware detection. "

        # Extract meta information
        meta_match = re.search(r'meta:(.*?)(?:strings:|condition:)', content, re.DOTALL)
        if meta_match:
            explanation += "It includes metadata describing the rule's purpose. "

        # Mention strings
        if 'strings:' in content:
            explanation += "It defines specific strings or patterns to match. "

        # Mention condition
        if 'condition:' in content:
            explanation += "The condition specifies when the rule should trigger based on the defined strings and patterns."

        return explanation

    def _explain_sigma_rule(self, content: str, title: str) -> str:
        """Generate explanation for Sigma rule"""
        explanation = f"This Sigma rule '{title}' is used for threat detection. "

        # Extract description
        desc_match = re.search(r'description:\s*(.+)', content)
        if desc_match:
            explanation += desc_match.group(1).strip()

        return explanation

    def _extract_yara_category(self, filename: str) -> str:
        """Extract category from YARA filename"""
        path_parts = Path(filename).parts
        if len(path_parts) > 1:
            return path_parts[0]
        return "malware"

    def _extract_sigma_category(self, filename: str) -> str:
        """Extract category from Sigma filename"""
        if 'process_creation' in filename:
            return "process creation"
        elif 'network' in filename:
            return "network"
        elif 'file' in filename:
            return "file system"
        else:
            return "system activity"

    def format_all_to_dataset(self, tools_docs: List[Dict], rules_data: Dict) -> str:
        """Format all data into a single JSONL dataset"""
        all_instructions = []

        # Process tool documentation
        print("\nFormatting tool documentation...")
        for tool_data in tools_docs:
            # README instructions
            readme_instructions = self.create_instruction_from_readme(tool_data)
            all_instructions.extend(readme_instructions)

            # Additional docs
            tool_name = tool_data.get('tool', {}).get('name', 'Unknown')
            metadata = tool_data.get('metadata', {})

            for doc in tool_data.get('docs', []):
                doc_instructions = self.create_instruction_from_doc(tool_name, doc, metadata)
                all_instructions.extend(doc_instructions)

        print(f"  Created {len(all_instructions)} instructions from tools")

        # Process YARA rules
        print("\nFormatting YARA rules...")
        yara_count = 0
        for rule in rules_data.get('yara', {}).get('rules', [])[:100]:  # Limit for dataset
            yara_instructions = self.create_yara_instructions(rule)
            all_instructions.extend(yara_instructions)
            yara_count += len(yara_instructions)

        print(f"  Created {yara_count} instructions from YARA rules")

        # Process Sigma rules
        print("\nFormatting Sigma rules...")
        sigma_count = 0
        for rule in rules_data.get('sigma', {}).get('rules', [])[:100]:  # Limit for dataset
            sigma_instructions = self.create_sigma_instructions(rule)
            all_instructions.extend(sigma_instructions)
            sigma_count += len(sigma_instructions)

        print(f"  Created {sigma_count} instructions from Sigma rules")

        # Save as JSONL
        output_file = self.output_dir / 'cybersecurity_instruct_dataset.jsonl'

        with open(output_file, 'w', encoding='utf-8') as f:
            for instruction in all_instructions:
                f.write(json.dumps(instruction, ensure_ascii=False) + '\n')

        print(f"\nDataset saved to: {output_file}")
        print(f"Total instructions: {len(all_instructions)}")

        # Also create a summary file
        summary = {
            'dataset_name': 'Cybersecurity OSS Tools Instruction Dataset',
            'created_at': datetime.now().isoformat(),
            'total_instructions': len(all_instructions),
            'sources': {
                'tools': len(tools_docs),
                'yara_rules': len(rules_data.get('yara', {}).get('rules', [])),
                'sigma_rules': len(rules_data.get('sigma', {}).get('rules', []))
            },
            'instruction_types': {
                'tool_documentation': sum(1 for i in all_instructions if i['metadata'].get('category') == 'cybersecurity'),
                'yara_rules': sum(1 for i in all_instructions if i['metadata'].get('category') == 'yara'),
                'sigma_rules': sum(1 for i in all_instructions if i['metadata'].get('category') == 'sigma')
            }
        }

        summary_file = self.output_dir / 'dataset_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"Summary saved to: {summary_file}")

        return str(output_file)
