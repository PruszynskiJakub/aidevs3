# This is the main entry point for the s3e1 module.

from services import OpenAiService, list_files

service = OpenAiService()

def main():
    print("Hello from s3e1!")
    
    # Build report from .txt files in the 'files' directory
    report = build_report()
    print("Report from .txt files:\n", report)
    
    # Build knowledge from facts
    knowledge = build_knowledge()
    print("Combined knowledge from facts:\n", knowledge)


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

async def situate_chunk(
    report_file_name: str, 
    chunk_content: str, 
    full_report: str, 
    facts: str
) -> str:
    """Situates a chunk of the report within the context of the full report and facts."""

    prompt = f'''<document>
                {full_report}
                </document>

                <facts>
                {facts}
                </facts>

                <chunk_filename>
                {report_file_name}
                </chunk_filename>

                <chunk>
                {chunk_content}
                </chunk>

                Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. 
                Answer only with the succinct context and nothing else.'''
    response = await service.completion(
        messages=[{
            'role': 'system',
            'content': prompt
        }]
    )
    return response.choices[0].message.content

async def describe_report(report_file_name: str, chunk_content: str, full_report: str, facts: str) -> str:
    """Describes a report by situating its content within the context of the provided full report and facts."""
    context = await situate_chunk(report_file_name, chunk_content, full_report, facts)
    return context
