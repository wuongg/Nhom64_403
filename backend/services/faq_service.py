import os
from pathlib import Path
from typing import Dict, List, Tuple
from ..parser import MarkdownParser

class FAQService:
    def __init__(self, raw_data_dir: str):
        self.raw_data_dir = Path(raw_data_dir)
        self.files = {
            "driver-bike": "xanhsm-driver-bike-faq.md",
            "driver-taxi": "xanhsm-driver-taxi-faq.md",
            "restaurant": "xanhsm-restaurant-faq.md",
            "user": "xanhsm-user-faq.md"
        }

    def get_structure_summary(self) -> str:
        """
        Returns a summary of all files and their H2 categories.
        Used by the Router Agent to decide where to look.
        """
        summary = []
        for key, filename in self.files.items():
            file_path = self.raw_data_dir / filename
            if file_path.exists():
                headers = MarkdownParser.get_all_headers(str(file_path))
                summary.append(f"File: {filename} (Key: {key})")
                for h in headers:
                    summary.append(f"  - Category: {h}")
        return "\n".join(summary)

    def get_context(self, file_key: str, category: str) -> str:
        """
        Retrieves the full text under a specific category in a file.
        """
        filename = self.files.get(file_key)
        if not filename:
            return ""
        
        file_path = self.raw_data_dir / filename
        if not file_path.exists():
            return ""
            
        sections = MarkdownParser.get_sections(str(file_path))
        # Find the header that closely matches (case insensitive or partial)
        for header, content in sections.items():
            if category.lower() in header.lower() or header.lower() in category.lower():
                return content
        
        return ""

    def get_sub_context(self, context: str, sub_topic: str) -> str:
        """
        Subdivides the context by H3 and returns the relevant part.
        """
        h3_sections = MarkdownParser.get_h3_sections(context)
        for header, content in h3_sections.items():
            if sub_topic.lower() in header.lower() or header.lower() in sub_topic.lower():
                return f"Topic: {header}\n\n{content}"
        return context # Fallback to full H2 context if no H3 matches
