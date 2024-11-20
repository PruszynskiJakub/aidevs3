import asyncio
import os
import sys

import requests
from dotenv import load_dotenv

from services import OpenAiService

# Add parent directory to Python path to find api module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import answer

load_dotenv()
API_KEY = os.getenv("AG3NTS_API_KEY")
DB_API_URL = "https://centrala.ag3nts.org/apidb"


def query_database(query: str) -> dict:
    response = requests.post(
        DB_API_URL,
        json={
            "task": "database",
            "apikey": API_KEY,
            "query": query
        }
    )
    return response.json()


async def get_sql_query(tables_info: dict) -> str:
    openai_service = OpenAiService()

    # Prepare the prompt with table structures
    prompt = """Based on the following database structure, create a SQL query that will find IDs of active datacenters 
    that are managed by inactive managers.

    Database structure:
    """
    for table, structure in tables_info.items():
        prompt += f"\n{table} table:\n{structure}\n"

    prompt += "\nRequirements:\n"
    prompt += "1. Find datacenter IDs where datacenter status is 'active'\n"
    prompt += "2. But the manager (user) status is 'inactive'\n"
    prompt += "3. Return only the datacenter IDs\n"
    prompt += "\nProvide only the SQL query, without any explanations and formatting. Skip any ```. Return pure sql query.\n"

    response = await openai_service.completion(
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()


async def main():
    # First, get the structure of relevant tables
    tables_info = {}

    # Get users table structure
    users_structure = query_database("show create table users")
    if users_structure.get('reply'):
        tables_info['users'] = users_structure['reply']

    # Get datacenters table structure
    datacenters_structure = query_database("show create table datacenters")
    if datacenters_structure.get('reply'):
        tables_info['datacenters'] = datacenters_structure['reply']

    # Get the SQL query from OpenAI
    sql_query = await get_sql_query(tables_info)
    print(f"Generated SQL query: {sql_query}")

    # Execute the query
    result = query_database(sql_query)
    print(f"Query result: {result}")

    if result.get('reply'):
        answer("database", [item['dc_id'] for item in result['reply']])
    else:
        print(f"Error: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
