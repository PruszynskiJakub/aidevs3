# This is the main entry point for the s3e1 module.

from services import OpenAiService, list_files

service = OpenAiService()

def main():
    print("Hello from s3e1!")
    
    # List files from the 'files' directory
    files = list_files('files')
    print("Files in 'files' directory:", files)
    
    # Build knowledge from facts
    knowledge = build_knowledge()
    print("Combined knowledge from facts:\n", knowledge)
    
import os

def build_report() -> str:
    """Builds a report by combining content from .txt files in the 'files' directory."""
    files = list_files('files')
    report_content = []
    for file_name in files:
        if file_name.endswith('.txt'):
            with open(f'files/{file_name}', 'r') as file:
                content = file.read().strip()
                report_content.append(f"<{file_name}>{content}</{file_name}>")
    return "\n".join(report_content)

def build_knowledge() -> str:

    """Builds a knowledge base by combining facts from the 'files/facts' directory."""
    facts = list_files('files/facts')
    combined_facts = []
    for fact_file in facts:
        with open(f'files/facts/{fact_file}', 'r') as file:
            content = file.read().strip()
            if content != "entry deleted":
                combined_facts.append(content)
    return "\n".join(combined_facts)

if __name__ == "__main__":
    main()
