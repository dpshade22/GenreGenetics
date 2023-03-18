import os
from flask import Flask, render_template, jsonify, redirect, send_from_directory
from flask_caching import Cache
import pandas as pd
import openai
from dotenv import load_dotenv

from UserGenes import UserGenes

load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)
# Configuring Flask-Caching settings
cache_config = {
    "CACHE_TYPE": "simple",  # Flask-Caching type
    "CACHE_DEFAULT_TIMEOUT": 360,  # Cache timeout in seconds (1 hour)
}

app.config.from_mapping(cache_config)
cache = Cache(app)

user = UserGenes()
user.initTracksDF()

topTracks = True

selectedDF = user.topTracksDF if topTracks else user.recentTracksDF

acronymExplanations = {
    "H": "High Energy",
    "L": "Low Energy",
    "P": "Positive Mood",
    "N": "Negative Mood",
    "F": "Fast Tempo",
    "S": "Slow Tempo",
    "E": "Electronic Instrumentation",
    "A": "Acoustic Instrumentation",
}

topOrRecent = "top" if topTracks else "recent"

promptForGPTMusicSummary = f"""
Given my {topOrRecent} tracks, artist names, album names, track duration 
preferences, explicit music preferences, singles or albums preferences, 
new or old music preferences, and genre distribution, provide a comprehensive 
summary of my music taste and listening habits.
"""

selectedDF
gptSummaryDF = selectedDF[
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

dfJSON = gptSummaryDF.to_json(orient="split", index=False)
gptSummaryDF.to_csv("topTracks.csv", index=False)
gptSummaryJSON = gptSummaryDF.to_json(orient="records")


@app.route("/")
@cache.cached(86400)
def index():
    # topTracksSummaryResp = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": promptForGPTMusicSummary,
    #         },
    #         {
    #             "role": "user",
    #             "content": gptSummaryJSON,
    #         },
    #     ],
    # )
    # topTracksSummaryText = topTracksSummaryResp["choices"][0]["message"]["content"]
    topTracksSummaryText = "Test"
    print(topTracksSummaryText)

    if not user.authManager.validate_token(user.authManager.get_cached_token()):
        auth_url = user.authManager.get_authorize_url()
        return redirect(auth_url)
    else:
        recentlyPlayedSongs = user.getRecentlyPlayedForCard()
        return render_template(
            "index.html",
            recentlyPlayedSongs=recentlyPlayedSongs,
            gptSummary=topTracksSummaryText,
        )


@app.route("/about")
def about():
    return render_template("about.html", title="About Genre Genetics")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.gif",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/chart_data")
@cache.cached()
def chart_data():

    data = user.getGeneDataFromDF(selectedDF)

    options = {}
    return jsonify({"data": data, "options": options})


@app.route("/songs/<genre>")
@cache.cached()
def songs(genre):

    songs_df = selectedDF[selectedDF["gene"] == genre]

    songs = songs_df[
        ["trackName", "spotifyURL", "artistNames", "artistLinks", "albumCoverURL"]
    ].to_dict("records")

    recommendations = user.getRecommendationsByGene(selectedDF, seed_genre=genre)
    genreAcronyms = [
        acronymExplanations[letter] for letter in genre if letter in acronymExplanations
    ]

    return render_template(
        "songs.html",
        genre=genre,
        songs=songs,
        acronym_explanations=acronymExplanations,
        recommendations=recommendations,
        # gptSummary=text,
    )


if __name__ == "__main__":
    app.run(debug=True)
