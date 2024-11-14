# AI Agent for Robot Authorization Protocol
import asyncio

import requests

from services import OpenAiService

service = OpenAiService()


def make_api_call(response):
    print(response)
    result = requests.get(
        url="https://xyz.ag3nts.org/verify",
        json=response
    )
    return result.json()


async def process_interaction(message):
    """
    Main function to process each interaction step.
    Uses make_api_call() for protocol communication and
    answer_question() for generating responses.

    Input message format:
    {
        "text": str,    # Message content
        "msgID": str    # Message ID
    }
    """

    # Rules for message processing:
    # 1. If starting conversation, send READY
    # 2. If receiving a question, use answer_question() to get response
    # 3. Always maintain RoboISO 2230 standards
    # 4. Keep msgID consistent within conversation

    try:
        if message is None:
            # Start conversation
            return make_api_call({
                "text": "READY",
                "msgID": "0"
            })

        # Process incoming message
        if "AUTH" in message["text"]:
            # Respond to AUTH command
            return make_api_call({
                "text": "READY",
                "msgID": message["msgID"]
            })

        # If message appears to be a question
        if "?" in message["text"] or any(
                q in message["text"].lower() for q in ["what", "when", "where", "how", "calculate"]):
            answer = await service.completion(
                messages=[
                    {
                        "role": "system",
                        "content": f'You are a helpful assistant. Answer with the given knowledge <knowledege>{ROBOT_KNOWLEDGE}</knowledege>'
                    },
                    {
                        "role": "user",
                        "content": f'What is the answer to the question? <question>{message["text"]}</question>'
                    }
                ]
            )
            return make_api_call({
                "text": answer.choices[0].message.content,
                "msgID": message["msgID"]
            })

        # If received OK, continue monitoring
        if message["text"] == "OK":
            return "OK"  # Await next interaction

        # Handle any other cases
        return make_api_call({
            "text": "READY",
            "msgID": message["msgID"] if message.get("msgID") else "0"
        })

    except Exception as e:
        # Always maintain protocol even during errors
        return make_api_call({
            "text": "ERROR",
            "msgID": message.get("msgID", "0")
        })


# Knowledge Base (RoboISO 2230 standards)
ROBOT_KNOWLEDGE = {
    "current_year": "1999",
    "poland_capital": "Kraków",
    "hitchhiker_number": "69",
    # "protocol_version": "RoboISO 2230",
    # "allowed_language": "English"
}

# Response Templates
RESPONSES = {
    "language_error": "ERROR: ENGLISH REQUIRED",
    "auth_error": "ERROR: UNAUTHORIZED",
    "format_error": "ERROR: INVALID FORMAT",
    "ready": "READY",
    "ok": "OK"
}


async def main_short():
    message = None
    while message != 'OK':
        response = await process_interaction(message)
        message = response
        print(message)


if __name__ == "__main__":
    asyncio.run(main_short())
