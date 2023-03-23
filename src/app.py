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

import spotipy
import openai
import pandas as pd
import pymongo
import pickle

from UserGenes import UserGenes


def load_env_variables():
    load_dotenv()
    openai.api_key = os.environ.get("OPENAI_API_KEY")


def init_user():
    user = UserGenes()
    user.initTracksDF()
    return user


def get_acronym_explanations():
    return {
        "H": "High Energy",
        "L": "Low Energy",
        "P": "Positive Mood",
        "N": "Negative Mood",
        "F": "Fast Tempo",
        "S": "Slow Tempo",
        "E": "Electronic Instrumentation",
        "A": "Acoustic Instrumentation",
    }


def get_selected_dataframe(user):
    df = user.recentTracksDF
    subset = ["trackName", "artistNames"]


    # Convert lists in the "artistNames" column to tuples or strings
    df["artistNames"] = df["artistNames"].apply(tuple)

    df = df.drop_duplicates(subset=subset)
    return df


def get_prompt_for_gpt_music_summary(genre=""):

    return f"""
    Your task is to create a personalized 4 sentence summary of your listener's 
    music taste that truly resonates with them. Use your analysis of 
    a specific number of songs to draw conclusions about their personality 
    traits, values, and even lifestyle. Make sure to use language that is 
    both clear and engaging, avoiding any technical jargon that could cause 
    confusion. To create a summary that truly connects with your listener, address 
    them directly and showcase examples of artists and songs that support your conclusions. 
    It's important to consider factors such as the popularity of the songs and artists to determine 
    if your listener is a mainstream or niche listener. By doing so, you'll be able to tailor your 
    summary to their unique tastes, making it a personalized experience that they won't forget! So, 
    let's get started and make your listener feel truly understood through the power of music.
    """


def get_gpt_summary_dataframe(selected_df):
    return selected_df[
        [
            "trackName",
            "trackPopularity",
            "trackDurationMs",
            "trackExplicit",
            "albumName",
            "albumType",
            "albumReleaseDate",
            "artistNames",
            "artistLinks",
            "artistGenres",
            "artistPopularity",
            "type",
            "track_href",
            "duration_ms",
            "time_signature",
            "gene",
        ]
    ][:20]


# Initialize environment variables and user object
load_env_variables()

# Initialize the Spotify OAuth object
auth_manager = SpotifyOAuth(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI"),
    scope='user-read-private user-read-email user-library-modify user-library-read user-top-read user-read-recently-played'
)

# Replace the following values with your own information


client = pymongo.MongoClient(os.environ.get("MONGO_URI"))
db = client[os.environ.get("MONGO_DB")]
print(db)

users_collection = db["Users"]
print(users_collection)

# Initialize Flask and configure Flask-Caching
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

cache_config = {
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 360,
}
app.config.from_mapping(cache_config)
cache = Cache(app)

global userDict

# Updated index route
@app.route("/", methods=["GET", "POST"])
@cache.cached(timeout=360)
def index():
    global userDict
    if "token_info" in session and auth_manager.validate_token(session["token_info"]):

        user = pickle.loads(session["user"])  # Deserialize the user object from the session
        user = userDict[session["user"]]
        selectedDF = get_selected_dataframe(user)
        
        promptForGPTMusicSummary = get_prompt_for_gpt_music_summary()
        gptSummaryDF = get_gpt_summary_dataframe(selectedDF)
        gptSummaryJSON = gptSummaryDF.to_json(orient="records")
        topTracksSummaryText = "Test"

        sidebarCards = user.getRecentlyPlayedForCard()

        return render_template(
            "index.html",
            sidebarCards=sidebarCards,
            gptSummary=topTracksSummaryText,
        )
    else:
        auth_url = auth_manager.get_authorize_url()
        return render_template("index.html", auth_url=auth_url)


# Callback route
@app.route("/callback")
def callback():
    code = request.args.get('code')
    # print(f"Code: {code}")  # Add this line to check the code value
    token_info = auth_manager.get_access_token(code)
    # print(f"Token Info: {token_info}")  # Add this line to check the token_info value
    if token_info:
        global userDict
        session["token_info"] = token_info
        auth_manager.token_info = token_info
        sp = spotipy.Spotify(auth_manager=auth_manager)

        # Initialize UserGenes object with authenticated Spotify object
        user = UserGenes(sp)
        
        # Store user information in the users collection
        user_data = {
            "spotify_id": sp.me()["id"],
            "access_token": token_info["access_token"],
            "refresh_token": token_info["refresh_token"],
            "expiration_time": token_info["expires_at"],
            # Add any additional user information that you want to store
        }
        users_collection.insert_one(user_data)
        
        return redirect(url_for("index"))
    else:
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
    user = pickle.loads(session["user"])
    user = userDict[session["user"]]
    
    sidebar_cards = user.getRecentlyPlayedForCard()
    return jsonify(sidebar_cards)


@app.route("/chart_data")
def chart_data():

    if "user" not in session:
        # Return an appropriate error message or redirect the user to the login page
        return "User not found in session", 404
    
    user = pickle.loads(session["user"])
    user = userDict[session["user"]]

    selectedDF = get_selected_dataframe(user)
    data = user.getGeneDataFromDF(selectedDF)

    options = {}
    return jsonify({"data": data, "options": options})


@app.route("/songs/<genre>")
@cache.cached()
def songs(genre):
    user = pickle.loads(session["user"])
    user = userDict[session["user"]]

    selectedDF = get_selected_dataframe(user)
    acronymExplanations = get_acronym_explanations()
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
        acronym_explanations=acronymExplanations,
        recommendations=recommendations,
        musicTasteSummary=topTracksSummaryText,
    )


@app.route("/generate_summary", methods=["POST"])
def generate_summary():
    user = pickle.loads(session["user"])
    user = userDict[session["user"]]

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
