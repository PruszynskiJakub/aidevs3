import asyncio
import json

from services import OpenAiService, list_files

service = OpenAiService()

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
    prompt = f'''Based on the following report and its context, generate a concise list of keywords that best represent the core topics and themes. 

    <context>
    {context}
    </context>

    <report>
    {chunk_content}
    </report>

    Ensure the keywords are relevant and capture the essence of the content provided. 
    The keywords must be nominatives in a single form. Generate between 5 and 10 keywords, separated by commas, with no additional formatting.'''
    response = await service.completion(
        messages=[{
            'role': 'system',
            'content': prompt
        }]
    )
    return response.choices[0].message.content


async def main():
    print("Hello from s3e1!")

    # Build the full report and knowledge base before processing files
    full_report = build_report()
    facts = build_knowledge()

    # Iterate over .txt files in the 'files' directory and build a JSON object
    files = list_files('files')
    keywords_dict = {}

    for file_name in files:
        if file_name.endswith('.txt'):
            with open(f'files/{file_name}', 'r') as file:
                chunk_content = file.read().strip()
                keywords = await describe_report(file_name, chunk_content, full_report, facts)
                keywords_dict[file_name] = keywords

    print("Keywords JSON:\n", json.dumps(keywords_dict, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
