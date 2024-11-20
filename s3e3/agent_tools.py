import os
from typing import TypedDict

import requests

import api
from services import OpenAiService


class GetTablesParams(TypedDict):
    _thoughts: str


class GetTableStructureParams(TypedDict):
    table_name: str
    _thoughts: str


async def get_tables(params: GetTablesParams) -> str:
    params.pop('_thoughts', None)
    response = requests.get(
        url=os.getenv('AG3NTS_HQ_URL') + '/apidb',
        json={
            "task": "database",
            "apikey": os.getenv('AG3NTS_API_KEY'),
            "query": "show tables"
        }
    )
    return response.json()


async def get_table_structure(params: GetTableStructureParams) -> str:
    params.pop('_thoughts', None)
    response = requests.get(
        url=os.getenv('AG3NTS_HQ_URL') + '/apidb',
        json={
            "task": "database",
            "apikey": os.getenv('AG3NTS_API_KEY'),
            "query": f"show create table {params['table_name']}"
        }
    )
    return response.json()


class ExecuteQueryParams(TypedDict):
    query: str
    _thoughts: str


async def execute_query(params: ExecuteQueryParams) -> str:
    params.pop('_thoughts', None)
    response = requests.get(
        url=os.getenv('AG3NTS_HQ_URL') + '/apidb',
        json={
            "task": "database",
            "apikey": os.getenv('AG3NTS_API_KEY'),
            "query": params['query']
        }
    )
    return response.json()


class AnalyzeStructureParams(TypedDict):
    table_structures: str
    task_description: str
    _thoughts: str


async def analyze_structure(params: AnalyzeStructureParams) -> str:
    params.pop('_thoughts', None)
    completion = await OpenAiService().completion(
        messages=[
            {
                "role": "system",
                "content": """You are a SQL expert. Your task is to analyze the database structure 
                and create an SQL query that will solve the given task. Focus on writing correct SQL 
                that will work with the given database structure. Return pure SQL, nothing else.
                
                Expected output format:
                <example>
                SELECT * FROM table_name;
                </example>
                """

            },
            {
                "role": "user",
                "content": f"""
                Given the following database structure:
                {params['table_structures']}
                
                Create an SQL query that will solve this task:
                {params['task_description']}
                
                Return only the SQL query, nothing else. No extra formatting, no ```. Return pure SQL.

                
                """
            }
        ]
    )
    return completion.choices[0].message.content


async def final_answer(ids: list[int]) -> str:
    result = api.answer("database", ids)
    return str(result)


tools = {
    'get_tables': get_tables,
    'get_table_structure': get_table_structure,
    'execute_query': execute_query,
    'analyze_structure': analyze_structure,
    'final_answer': final_answer
}
