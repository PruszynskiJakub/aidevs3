from flask import Flask, request, jsonify

from services import OpenAiService

service = OpenAiService()
app = Flask(__name__)


@app.route('/api/chat', methods=['POST'])
async def chat():
    data = request.get_json()
    messages = data.get('messages', [])
    model = data.get('model', 'gpt-4o')

    try:
        token_count = await service.count_tokens(messages)
        print(f"Token count for model {model}: {token_count}")
        return jsonify({'tokenCount': token_count, 'model': model})
    except Exception as error:
        print('Error in token counting:', error)
        return jsonify({'error': 'An error occurred while processing your request'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=3000)
