import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")
msg = ""

resp = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "system",
            "content": "Please generate a short summary of my music taste based on the following: Genre: {genre}, Songs: {songs}, Artists: {artists}",
        },
        {"role": "user", "content": msg},
    ],
)

text = resp["choices"][0]["message"]["content"]
