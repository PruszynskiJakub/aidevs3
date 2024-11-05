from flask import Flask, request, jsonify
from openai.types.chat import ChatCompletionMessageParam

from examples.thread.OpenAiService import OpenAiService

service = OpenAiService()
app = Flask(__name__)

previous_summarization = ""


async def generate_summarization(user_msg: ChatCompletionMessageParam,
                                 assistant_response: ChatCompletionMessageParam) -> str:
    summarization_prompt = {
        "role": "system",
        "content": f'''Please summarize the following conversation in a concise manner, incorporating the previous summary if available:
            <previous_summary>{previous_summarization or "No previous summary"}</previous_summary>
            <current_turn> Kuba: {user_msg['content']}\n AI: {assistant_response.content} </current_turn>'''
    }

    response = await service.completion(
        messages=[summarization_prompt, {"role": "user", "content": "Please create/update our conversation summary."}],
        model="gpt-4o-mini",
        stream=False
    )

    return response.choices[0].message.content or "No summarization found"


def create_system_prompt(summarization: str) -> ChatCompletionMessageParam:
    return {
        "role": "system",
        "content": f"""You are AI, a helpful assistant who speaks using as few words as possible.
        {"Here is a summary of the conversation so far: \n<conversation_summary>\n  " + summarization + "\n</conversation_summary>" if summarization else ''}
        Let's chat!"""
    }


@app.route('/api/chat', methods=['POST'])
async def chat():
    message = request.json

    try:
        global previous_summarization
        assistant_response = await service.completion(
            messages=[create_system_prompt(previous_summarization), message],
            model="gpt-4o-mini",
            stream=False
        )

        previous_summarization = await generate_summarization(message, assistant_response.choices[0].message)
        return assistant_response.model_dump()
    except Exception as e:
        raise e


@app.route('/api/demo', methods=['POST'])
async def demo():
    global previous_summarization
    demo_messages = [
        {"content": "Hi! I'm Adam", "role": "user"},
        {"content": "How are you?", "role": "user"},
        {"content": "Do you know my name?", "role": "user"}
    ]

    assistant_response = None

    for message in demo_messages:
        print('--- NEXT TURN ---')
        print('Adam:', message['content'])
        assistant_response: ChatCompletionMessageParam or None = None
        try:
            system_prompt = create_system_prompt(previous_summarization)

            assistant_response = await service.completion(
                [system_prompt, message],
                "gpt-4o",
                False
            )

            print('Alice:', assistant_response.choices[0].message.content)

            # Generate new summarization
            previous_summarization = await generate_summarization(message, assistant_response.choices[0].message)
        except Exception as error:
            print('Error in OpenAI completion:', str(error))
            return jsonify({"error": "An error occurred while processing your request"}), 500

    return jsonify(assistant_response.choices[0].model_dump())


if __name__ == '__main__':
    app.run(debug=True, port=3000)
