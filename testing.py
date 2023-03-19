import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")
msg = "Summarize my music taste"
summ = '[{"trackName":"Fruit&Sun","trackPopularity":"51 (0-100)","trackDurationMs":"177857 ms","trackExplicit":false,"albumName":"The Color of Nothing","albumType":"album","albumReleaseDate":"2020-10-16","artistNames":["ford."],"artistLinks":["https:\/\/open.spotify.com\/artist\/7ItbAZITSFxSy5LJChXe18"],"artistGenres":["new french touch","vapor soul","vapor twitch"],"artistPopularity":"56 (0-100)","type":"audio_features","track_href":"https:\/\/api.spotify.com\/v1\/tracks\/69cmKJCT4thXR1qT1g34w7","duration_ms":177857,"time_signature":4,"gene":"HNFA"},{"trackName":"belong","trackPopularity":"50 (0-100)","trackDurationMs":"173493 ms","trackExplicit":false,"albumName":"komorebi","albumType":"album","albumReleaseDate":"2019-09-20","artistNames":["slenderbodies"],"artistLinks":["https:\/\/open.spotify.com\/artist\/3S4d3YRNGg2OhnNm3QvfhA"],"artistGenres":["indie poptimism","indie soul","vapor soul"],"artistPopularity":"54 (0-100)","type":"audio_features","track_href":"https:\/\/api.spotify.com\/v1\/tracks\/33n1o7mzohXiCzS6Rr5q2E","duration_ms":173493,"time_signature":4,"gene":"HNFA"}]'

resp = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "system",
            "content": f"You are a magic genie who knows about your user's music taste. Try to use as much information from the following in order to answer their questions. ",
        },
        {"role": "user", "content": f"{msg}. Here is some of my music: {summ}"},
    ],
)
text = resp["choices"][0]["message"]["content"]

print(text)
