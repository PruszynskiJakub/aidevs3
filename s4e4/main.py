import asyncio
import json

from flask import Flask, request, jsonify

from services import OpenAiService

app = Flask(__name__)

# Initialize OpenAI service
ai_service = OpenAiService()

# This will be our map description prompt - we'll fill it later
MAP_DESCRIPTION = """
# Polish Language 4x4 Map Navigation System

<prompt_objective>
Process Polish language movement instructions on a 4x4 map, tracking position changes from a starting point (1,1) and return the description of the endpoint location.
</prompt_objective>

<map_layout>
1,1 (top-left) - starting point
1,2 - trawa
1,3 - trawa
1,4 - skały
2,1 - trawa
2,2 - wiatrak
2,3 - trawa
2,4 - skały
3,1 - drzewo
3,2 - trawa
3,3 - skały
3,4 - samochód
4,1 - dom
4,2 - trawa
4,3 - dwa drzewa
4,4 - jaskinia
</map_layout>

<prompt_rules>
1. ALWAYS start from position 1,1 (top-left corner)
2. Movement instructions MUST be in Polish
3. Valid directional commands:
   - "w prawo" (right)
   - "w lewo" (left)
   - "w dół" (down)
   - "w górę" (up)
   - "na sam dół" (all the way down)
   - "na samą górę" (all the way up)
   - "do końca w lewo" (all the way left)
   - "do końca w prawo" (all the way right)
4. Grid boundaries are 4x4 (coordinates 1-4)
5. When encountering invalid movement (outside grid):
   - STOP at the last valid position
   - Include reasoning about why movement stopped
6. For compound movements:
   - Process each movement separately
   - Include each step in the output
7. ALL thinking and reasoning MUST be in English
8. Terrain types are fixed as shown in the map layout
</prompt_rules>

<directions_rules>
UP - "w górę" - Move up one field - from (x,y) to (x,y-1)
DOWN - "w dół" - Move down one field - from (x,y) to (x,y+1)
LEFT - "w lewo" - Move left one field - from (x,y) to (x-1,y)
RIGHT - "w prawo" - Move right one field - from (x,y) to (x+1,y)
</directions_rules>

<output_format>
Response MUST be valid JSON with the following structure:
{
    "_thinking": "String explaining step-by-step reasoning in English",
    "steps": {
        "1": "Description of first movement with coordinates",
        "2": "Description of second movement with coordinates",
        ...
    },
    "reasoning": "String explaining final position analysis in English",
    "description": "String containing terrain type in Polish from the map"
}
</output_format>

<prompt_examples>
1. Simple Movement:
Input: {"instruction": "w prawo"}
Output: {
    "_thinking": "Moving one step right from starting position (1,1)",
    "steps": {
        "1": "Move right (x+1,y) from (1,1) to (2,1)"
    },
    "reasoning": "Reached field (2,1)",
    "description": "trawa"
}

2. Complex Movement:
Input: {"instruction": "w prawo, na sam dół"}
Output: {
    "_thinking": "First moving right, then all the way down",
    "steps": {
        "1": "Move right (x+1,y) from (1,1) to (2,1)",
        "2": "Move down (x,y+1) from (2,1) to (2,2)",
        "3": "Move down (x,y+1) from (2,2) to (2,3)",
        "4": "Move down (x,y+1) from (2,3) to (2,4)"
    },
    "reasoning": "Reached bottom row at position (2,4)",
    "description": "skały"
}

3. Invalid Movement:
Input: {"instruction": "w lewo"}
Output: {
    "_thinking": "Cannot move left from starting position (1,1) as it would be outside the grid",
    "steps": {},
    "reasoning": "Staying at starting position as movement is invalid: (x-1,y) would result in (0,1), which is out of bounds",
    "description": "starting point"
}

4. Full Traversal:
Input: {"instruction": "na sam dół, do końca w prawo"}
Output: {
    "_thinking": "Moving all the way down first, then all the way right",
    "steps": {
        "1": "Move down (x,y+1) from (1,1) to (1,2)",
        "2": "Move down (x,y+1) from (1,2) to (1,3)",
        "3": "Move down (x,y+1) from (1,3) to (1,4)",
        "4": "Move right (x+1,y) from (1,4) to (2,4)",
        "5": "Move right (x+1,y) from (2,4) to (3,4)",
        "6": "Move right (x+1,y) from (3,4) to (4,4)"
    },
    "reasoning": "Reached bottom-right corner at position (4,4)",
    "description": "jaskinia"
}
</prompt_examples>

<error_handling>
1. For invalid movements:
   - Return current position's description
   - Explain why movement cannot continue
   - Include any valid steps that were completed before the invalid movement
2. For unrecognized commands:
   - Stay at current position
   - Explain that command is not recognized
3. For empty or invalid input:
   - Return starting position description
   - Include explanation of the error
</error_handling>
"""


async def get_location_description(instruction):
    """
    Get location description based on flight instruction using OpenAI API
    """
    messages = [
        {"role": "system", "content": MAP_DESCRIPTION},
        {"role": "user",
         "content": f"Based on the flight instruction: '{instruction}', what is at the final location? Respond with maximum two words."}
    ]

    try:
        response = await ai_service.completion(
            messages=messages,
            response_format={"type": "json_object"}
        )
        print(response.choices[0].message.content)

        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "error occurred"


@app.route('/', methods=['POST'])
def process_instruction():
    """
    Process incoming drone flight instructions
    """
    try:
        data = request.get_json()

        if not data or 'instruction' not in data:
            return jsonify({"error": "Missing instruction in request"}), 400

        instruction = data['instruction']
        print(f"Received instruction: {instruction}")
        # Run the async function in the synchronous Flask route
        location_description = asyncio.run(get_location_description(instruction))

        return jsonify({
            "description": location_description['description'],
            "debug": {
                "received_instruction": instruction
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
