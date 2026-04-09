import re
from pathlib import Path
from typing import Dict, List, Optional

class MarkdownParser:
    @staticmethod
    def get_sections(file_path: str) -> Dict[str, str]:
        """
        Parses a markdown file and returns a dictionary where keys are H2 headers 
        and values are the content under that header (until the next H2).
        """
        content = Path(file_path).read_text(encoding="utf-8")
        
        # Split by H2 headers (##)
        # We use a regex that looks for ## at the start of a line
        sections = {}
        current_header = "Intro"
        current_content = []
        
        lines = content.splitlines()
        for line in lines:
            h2_match = re.match(r"^##\s+(.*)", line)
            if h2_match:
                if current_content:
                    sections[current_header] = "\n".join(current_content).strip()
                current_header = h2_match.group(1).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add the last section
        if current_content:
            sections[current_header] = "\n".join(current_content).strip()
            
        return sections

    @staticmethod
    def get_h3_sections(section_text: str) -> Dict[str, str]:
        """
        Takes a block of text (usually from an H2 section) and further 
        subdivides it by H3 headers (###).
        """
        sections = {}
        current_header = "General"
        current_content = []
        
        lines = section_text.splitlines()
        for line in lines:
            h3_match = re.match(r"^###\s+(.*)", line)
            if h3_match:
                if current_content:
                    sections[current_header] = "\n".join(current_content).strip()
                current_header = h3_match.group(1).strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_header] = "\n".join(current_content).strip()
            
        return sections

    @staticmethod
    def get_all_headers(file_path: str) -> List[str]:
        """Returns all H2 headers in a file."""
        content = Path(file_path).read_text(encoding="utf-8")
        return re.findall(r"^##\s+(.*)", content, re.MULTILINE)
