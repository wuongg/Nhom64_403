import sys
import os
import io

# Fix encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current dir to sys.path to import from backend
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.services.faq_service import FAQService
from backend.parser import MarkdownParser

def test_parser():
    print("--- Testing Parser ---")
    test_file = "raw/xanhsm-user-faq.md"
    if not os.path.exists(test_file):
        print(f"File {test_file} not found!")
        return
    
    headers = MarkdownParser.get_all_headers(test_file)
    print(f"Found {len(headers)} H2 headers: {headers[:3]}...")
    
    sections = MarkdownParser.get_sections(test_file)
    first_header = list(sections.keys())[1] # Skip Intro
    print(f"Content under '{first_header}': {sections[first_header][:100]}...")

def test_service():
    print("\n--- Testing FAQ Service ---")
    service = FAQService("raw")
    summary = service.get_structure_summary()
    print("Structure Summary Preview:")
    print("\n".join(summary.splitlines()[:10]))
    
    print("\nTesting context retrieval for 'user' file, 'An toàn' category:")
    context = service.get_context("user", "An toàn")
    if context:
        print(f"Retrieved {len(context)} characters.")
        print(f"Preview: {context[:200]}...")
    else:
        print("Failed to retrieve context!")

if __name__ == "__main__":
    test_parser()
    test_service()
