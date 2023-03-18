import os
from flask import Flask, render_template, jsonify, redirect, send_from_directory
from flask_caching import Cache
import pandas as pd


from UserGenes import UserGenes

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

acronym_explanations = {
    "H": "High Energy",
    "L": "Low Energy",
    "P": "Positive Mood",
    "N": "Negative Mood",
    "F": "Fast Tempo",
    "S": "Slow Tempo",
    "E": "Electronic Instrumentation",
    "A": "Acoustic Instrumentation",
}


@app.route("/")
@cache.cached()
def index():
    if not user.authManager.validate_token(user.authManager.get_cached_token()):
        auth_url = user.authManager.get_authorize_url()
        return redirect(auth_url)
    else:
        recentlyPlayedSongs = user.getRecentlyPlayed()
        return render_template("index.html", recentlyPlayedSongs=recentlyPlayedSongs)


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
    data = user.getGeneData()
    options = {}
    return jsonify({"data": data, "options": options})


@app.route("/songs/<genre>")
@cache.cached()
def songs(genre):
    songs_df = user.getPrettyGenreDF(genre)
    songs = songs_df[
        ["trackName", "trackLink", "artists", "artistLink", "albumCoverURL"]
    ].to_dict("records")

    print(songs)
    recommendations = user.getRecommendationsByGene(seed_genre=genre)
    print(recommendations[3])
    return render_template(
        "songs.html",
        genre=genre,
        songs=songs,
        acronym_explanations=acronym_explanations,
        recommendations=recommendations,
    )


if __name__ == "__main__":
    app.run(debug=True)
