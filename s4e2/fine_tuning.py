import os

import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai.api_key)

# Define the training file ID and the model to fine-tune
training_file_id = "file-8HKwCmnESTZyhKhUrDd1QW"  # Replace with your training file ID
validation_file_id = "file-94fffYePcnwkBZ2pdfyCef"  # Replace with your training file ID
model_to_fine_tune = "gpt-4o-mini-2024-07-18"  # Replace with your desired model

try:
    # Create a fine-tuning job
    fine_tune_job = client.fine_tuning.jobs.create(
        model=model_to_fine_tune,
        training_file=training_file_id,
        # validation_file=validation_file_id,
        # validation_fraction=0.1,
    )
    print("Fine-tuning job created successfully!")

except openai.APIConnectionError as e:
    print("The server could not be reached.")
    print(e)
except openai.RateLimitError as e:
    print("Rate limit exceeded; please wait and try again.")
    print(e)
except openai.APIError as e:
    print(f"An API error occurred: {e}")
