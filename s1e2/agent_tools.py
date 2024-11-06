import os
from typing import TypedDict

import requests

from OpenAiService import OpenAiService


class MakeApiCallParams(TypedDict):
    payload: str


async def make_api_call(params: MakeApiCallParams) -> str:
    params.pop('_thoughts')
    response = requests.get(
        url=os.getenv('AG3NTS_URL_VERIFY'),
        json=params
    )
    return response.json()


class AnswerQuestionParams(TypedDict):
    question: str


async def answer_question(params: AnswerQuestionParams) -> str:
    return "Answer to the question"


class AttainKnowledgeParams(TypedDict):
    filename: str
    query_context: str


async def attain_knowledge(params: AttainKnowledgeParams) -> str:
    file_content = read_file(params['filename'])
    completion = await OpenAiService().completion(
        messages=[
            {
                "role": "system",
                "content": f'''You are a true expert in summarization like a pro detective. 
                Summarize the following text by extracting key information and main points from the provided *content*.
                Your summary should be concise and to the point and be based on the user's query *query_context*.
                Keep in mind that all the result will be used a base for a super important task.
    
                
                <query_context>
                {params['query_context']}
                </query_context>
                
                <content>
                {file_content}
                </content>
                
                
                Please remember that it's super important to be thorough and accurate in your summary.
                Let's get started!
                '''
            },
        ]
    )
    return completion.choices[0].message.content


def read_file(filename: str) -> str:
    with open(filename, 'r') as file:
        return file.read()


# class SummarizeParams(TypedDict):
#     context_query: str
#     knowledge: str
#
# async def summarize(params: SummarizeParams) -> str:
#     completion = await OpenAiService().completion(
#         messages = [
#             {
#                 "role": "system",
#                 "content": "You are a helpful assistant.Be concise and hyper focused on the main points and key details."
#             },
#             {
#                 "role": "user",
#                 "content": f"Summarize the following text {params['knowledge']} from the given context {params['context_query']}"
#             }
#         ]
#     )
#     return completion.choices[0].message.content

tools = {
    'make_api_call': make_api_call,
    'answer_question': answer_question,
    'attain_knowledge': attain_knowledge,
    # 'summarize': summarize
}
