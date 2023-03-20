import openai
import os
from dotenv import load_dotenv

load_dotenv()
import openai
import os
from dotenv import load_dotenv
import pandas as pd
from src.UserGenes import UserGenes

load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")


def parse_spotify_data(df):
    url_cols = [
        "spotifyURL",
        "artistLinks",
        "artistGenres",
        "artistID",
        "analysis_url",
        "track_href",
        "uri",
        "albumCoverURL",
        "id",
    ]
    non_url_cols = [col for col in df.columns if col not in url_cols]
    return df[non_url_cols].to_dict(orient="records")


def get_top_tracks():
    userGenes = UserGenes()
    userGenes.authenticate()
    userGenes.initTracksDF()
    top_tracks = userGenes.topTracksDF.head(10)
    return parse_spotify_data(top_tracks)


messages = [
    {
        "role": "system",
        "content": f"You are a personalized music taste assistant. Try to use as much information from the following in order to answer their questions.",
    },
    {
        "role": "user",
        "content": f"Here are my top tracks: {get_top_tracks()}",
    },
    {
        "role": "assistant",
        "content": "Thanks for sharing your top tracks information! What questions do you have about your music?",
    },
]

while True:
    msg = input("Enter your message: ")
    messages.append({"role": "user", "content": f"{msg}"})
    if "top tracks" in msg.lower():
        num_tracks = int(msg.split()[-1])
        top_tracks = get_top_tracks(num_tracks)
        messages.append(
            {
                "role": "assistant",
                "content": f"Here are your top {num_tracks} tracks: {top_tracks}",
            }
        )
    else:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        text = resp["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": f"{text}"})
    print(text)
