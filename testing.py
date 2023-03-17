import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd
import json

load_dotenv()

# Set environment variables
os.environ["SPOTIPY_CLIENT_ID"]
os.environ["SPOTIPY_CLIENT_SECRET"]
os.environ["SPOTIPY_REDIRECT_URI"]

# Authenticate with Spotify
auth_manager = SpotifyOAuth(
    scope="user-library-read user-top-read user-read-recently-played",
    redirect_uri="http://localhost:8000/callback/",
)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Get user's top artists
top_artists = sp.current_user_top_artists(limit=50)

# Get user's top tracks
top_tracks = sp.current_user_top_tracks(limit=50)

# Get user's recently played tracks
recently_played = sp.current_user_recently_played(limit=50)

# Combine data into a single list of dictionaries
data = []
for item in top_artists["items"]:
    data.append(
        {
            "type": "artist",
            "name": item["name"],
            "id": item["id"],
            "genres": item["genres"],
            "popularity": item["popularity"],
        }
    )
for item in top_tracks["items"]:
    # Get audio features for each track
    audio_features = sp.audio_features(item["id"])[0]

    data.append(
        {
            "type": "track",
            "name": item["name"],
            "id": item["id"],
            "artists": [artist["name"] for artist in item["artists"]],
            "album": item["album"]["name"],
            "popularity": item["popularity"],
            "acousticness": audio_features["acousticness"],
            "danceability": audio_features["danceability"],
            "energy": audio_features["energy"],
            "instrumentalness": audio_features["instrumentalness"],
            "key": audio_features["key"],
            "liveness": audio_features["liveness"],
            "loudness": audio_features["loudness"],
            "mode": audio_features["mode"],
            "speechiness": audio_features["speechiness"],
            "tempo": audio_features["tempo"],
            "valence": audio_features["valence"],
        }
    )
for item in recently_played["items"]:
    track = item["track"]

    # Get audio features for each track
    audio_features = sp.audio_features(track["id"])[0]

    data.append(
        {
            "type": "recent",
            "name": track["name"],
            "id": track["id"],
            "artists": [artist["name"] for artist in track["artists"]],
            "album": track["album"]["name"],
            "popularity": None,
            "acousticness": audio_features["acousticness"],
            "danceability": audio_features["danceability"],
            "energy": audio_features["energy"],
            "instrumentalness": audio_features["instrumentalness"],
            "key": audio_features["key"],
            "liveness": audio_features["liveness"],
            "loudness": audio_features["loudness"],
            "mode": audio_features["mode"],
            "speechiness": audio_features["speechiness"],
            "tempo": audio_features["tempo"],
            "valence": audio_features["valence"],
        }
    )

# Create dataframe from data
df = pd.DataFrame(data)
df.to_csv("data.csv", index=False)
