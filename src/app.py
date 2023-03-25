import os
import secrets
from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_caching import Cache
from spotipy.oauth2 import SpotifyOAuth

from datetime import datetime
import spotipy
import openai
import pandas as pd
import pymongo
import pickle

from UserGenes import UserGenes
from functions import (
    get_selected_dataframe,
    get_prompt_for_gpt_music_summary,
    get_gpt_summary_dataframe,
    load_env_variables,
)  # Initialize environment variables and user object

load_env_variables()

# Initialize the Spotify OAuth object
auth_manager = SpotifyOAuth(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI"),
    scope="user-read-private user-read-email user-library-modify user-library-read user-top-read user-read-recently-played",
)

user = UserGenes(sp=spotipy.Spotify(auth_manager=auth_manager))
user.initTracksDF()

# Initialize Flask and configure Flask-Caching
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

cache_config = {
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 360,
}
app.config.from_mapping(cache_config)
cache = Cache(app)

user_data = True


@app.route("/", methods=["GET", "POST"])
@cache.cached(timeout=360)
def index():
    try:
        if user_data:
            print("User data found in the database.")

            # Use the token info from the cookie to authenticate the Spotify API client
            sp = spotipy.Spotify(auth_manager=auth_manager)

            user = UserGenes(sp)
            selected_df = get_selected_dataframe(user)

            prompt_for_gpt_music_summary = get_prompt_for_gpt_music_summary()
            gpt_summary_df = get_gpt_summary_dataframe(selected_df)
            gpt_summary_json = gpt_summary_df.to_json(orient="records")
            top_tracks_summary_text = "Test"

            sidebar_cards = user.getRecentlyPlayedForCard()

            return render_template(
                "index.html",
                sidebar_cards=sidebar_cards,
                gpt_summary=top_tracks_summary_text,
            )
        else:
            print("User data not found in the database.")
            auth_url = auth_manager.get_authorize_url()
            return render_template("index.html", auth_url=auth_url)

    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = (
            "An error occurred while processing your request. Please try again later."
        )
        return render_template("index.html", error_message=error_message)


@app.route("/callback")
def callback():
    try:
        code = request.args.get("code")
        token_info = auth_manager.get_access_token(code)
        if token_info:
            sp = spotipy.Spotify(auth_manager=auth_manager)

            # Get user's profile information
            user_profile = sp.me()

            session["token_info"] = token_info

            return redirect(url_for("index"))
        else:
            print("Error: Failed to get access token.")
            return "Error: Failed to get access token", 400
    except Exception as e:
        print(f"Error: {e}")
        return "Error: Failed to get access token", 400


@app.route("/about")
def about():
    return render_template("about.html", title="About Genre Genetics")


@app.route("/chatbot")
def chatbot():
    return render_template(
        "chatbot.html", OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")
    )


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.gif",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/sidebar_card_data")
def sidebar_card_data():
    sidebar_cards = user.getRecentlyPlayedForCard()
    return jsonify(sidebar_cards)


@app.route("/chart_data")
def chart_data():
    print("HELLO", session)
    try:
        selectedDF = get_selected_dataframe(user)
        data = user.getGeneDataFromDF(selectedDF)

        options = {}
        return jsonify({"data": data, "options": options})
    except Exception as e:
        print(f"Error: {e}")
        return "Error occurred", 500


@app.route("/songs/<genre>")
@cache.cached()
def songs(genre):
    selectedDF = get_selected_dataframe(user)
    selectedDF = selectedDF[selectedDF["gene"] == genre]

    songs = selectedDF[
        ["trackName", "spotifyURL", "artistNames", "artistLinks", "albumCoverURL"]
    ].to_dict("records")

    recommendations = user.getRecommendationsByGene(
        selectedDF.reset_index(drop=True), seed_genre=genre
    )

    promptForGPTMusicSummary = get_prompt_for_gpt_music_summary(genre=genre)
    gptSummaryDF = get_gpt_summary_dataframe(selectedDF)
    gptSummaryJSON = gptSummaryDF.to_json(orient="records")

    topTracksSummaryText = "Test"
    return render_template(
        "songs.html",
        genre=genre,
        songs=songs,
        recommendations=recommendations,
        musicTasteSummary=topTracksSummaryText,
    )


@app.route("/generate_summary", methods=["POST"])
def generate_summary():
    selectedDF = get_selected_dataframe(user)

    promptForGPTMusicSummary = get_prompt_for_gpt_music_summary()

    # Construct the messages for the GPT-3.5 request
    messages = [
        {
            "role": "system",
            "content": promptForGPTMusicSummary,
        },
        {
            "role": "user",
            "content": f"Here is a list of my recently listened to tracks",
        },
    ]

    # Add the selected dataframe to the messages
    messages[1]["content"] += selectedDF.to_json(orient="records")

    # Send the request to GPT-3.5
    topTracksSummaryResp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    topTracksSummaryText = topTracksSummaryResp["choices"][0]["message"]["content"]

    return jsonify({"summary": topTracksSummaryText})


if __name__ == "__main__":
    app.run(debug=True)
