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
    df = user.topTracksDF if top_tracks else user.recentTracksDF
    subset = ["trackName", "artistNames"]

    # Convert lists in the "artistNames" column to tuples or strings
    df["artistNames"] = df["artistNames"].apply(tuple)

    df = df.drop_duplicates(subset=subset)
    return df


def get_prompt_for_gpt_music_summary(top_tracks, genre=""):
    top_or_recent = "top" if top_tracks else "recent"
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


@app.route("/", methods=["GET", "POST"])
@cache.cached(timeout=3600)  # Cache for 1 hour
def index():
    session["top_tracks"] = False
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
    #             "content": f"Here is a list of my {'top listened to tracks' if top_tracks else 'recently listened to tracks'}{gptSummaryJSON}",
    #         },
    #     ],
    # )
    # topTracksSummaryText = topTracksSummaryResp["choices"][0]["message"]["content"]
    topTracksSummaryText = "Test"

    if not user.authManager.validate_token(user.authManager.get_cached_token()):
        auth_url = user.authManager.get_authorize_url()
        return redirect(auth_url)
    else:
        sidebarCards = (
            user.getTopTracksForCard()
            if top_tracks
            else user.getRecentlyPlayedForCard()
        )

        print(sidebarCards)

        return render_template(
            "index.html",
            top_tracks=top_tracks,
            sidebarCards=sidebarCards,
            gptSummary=topTracksSummaryText,
        )


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
    top_tracks = get_top_tracks_status()
    print(f"top_tracks: {top_tracks}")
    selectedDF = get_selected_dataframe(user, get_top_tracks_status())
    acronymExplanations = get_acronym_explanations()
    selectedDF = selectedDF[selectedDF["gene"] == genre]

    songs = selectedDF[
        ["trackName", "spotifyURL", "artistNames", "artistLinks", "albumCoverURL"]
    ].to_dict("records")

    recommendations = user.getRecommendationsByGene(selectedDF, seed_genre=genre)
    promptForGPTMusicSummary = get_prompt_for_gpt_music_summary(
        top_tracks=top_tracks, genre=genre
    )
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
    return render_template(
        "songs.html",
        genre=genre,
        songs=songs,
        acronym_explanations=acronymExplanations,
        recommendations=recommendations,
        musicTasteSummary=topTracksSummaryText,
    )


if __name__ == "__main__":
    app.run(debug=True)
