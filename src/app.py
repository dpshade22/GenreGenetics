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
import openai
import pandas as pd

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


def get_selected_dataframe(user, top_tracks):
    return user.topTracksDF if top_tracks else user.recentTracksDF


def get_prompt_for_gpt_music_summary(top_tracks):
    top_or_recent = "top" if top_tracks else "recent"
    return f"""
    Given my {top_or_recent} tracks, artist names, album names, track duration 
    preferences, explicit music preferences, singles or albums preferences, 
    new or old music preferences, and genre distribution, provide a comprehensive 
    summary of my music taste and listening habits.
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
user = init_user()

# Initialize Flask and configure Flask-Caching
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

cache_config = {
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 360,
}
app.config.from_mapping(cache_config)
cache = Cache(app)

# Set global variables
def get_top_tracks_status():
    return session.get("top_tracks", False)


# Your app routes and the rest of the code


@app.route("/", methods=["GET", "POST"])
# @cache.cached(86400)
def index():
    session["top_tracks"] = True
    top_tracks = get_top_tracks_status()
    selectedDF = get_selected_dataframe(user, top_tracks)

    if request.method == "POST":
        top_tracks = request.form.get("top_tracks") == "True"
        session["top_tracks"] = not top_tracks
        return redirect(url_for("index"))

    selectedDF = get_selected_dataframe(user, top_tracks)

    promptForGPTMusicSummary = get_prompt_for_gpt_music_summary(top_tracks)
    gptSummaryDF = get_gpt_summary_dataframe(selectedDF)
    gptSummaryJSON = gptSummaryDF.to_json(orient="records")

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
    print(top_tracks)

    if not user.authManager.validate_token(user.authManager.get_cached_token()):
        auth_url = user.authManager.get_authorize_url()
        return redirect(auth_url)
    else:
        sidebarCards = (
            user.getTopTracksForCard()
            if top_tracks
            else user.getRecentlyPlayedForCard()
        )

        return render_template(
            "index.html",
            top_tracks=top_tracks,
            sidebarCards=sidebarCards,
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


@app.route("/sidebar_card_data")
def sidebar_card_data():
    top_tracks = request.args.get("top_tracks", "True") == "True"
    sidebar_cards = (
        user.getTopTracksForCard() if top_tracks else user.getRecentlyPlayedForCard()
    )
    return jsonify(sidebar_cards)


@app.route("/chart_data")
def chart_data():
    top_tracks = request.args.get("top_tracks", "True") == "True"
    selectedDF = get_selected_dataframe(user, top_tracks)
    data = user.getGeneDataFromDF(selectedDF)

    options = {}
    return jsonify({"data": data, "options": options})


@app.route("/select_top_tracks", methods=["POST"])
def select_top_tracks():
    top_tracks = request.form.get("top_tracks") == "True"
    session["top_tracks"] = top_tracks
    return redirect("/")


@app.route("/songs/<genre>")
@cache.cached()
def songs(genre):
    selectedDF = get_selected_dataframe(user, get_top_tracks_status())
    acronymExplanations = get_acronym_explanations()
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
