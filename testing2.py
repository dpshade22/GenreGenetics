from src.UserGenes import UserGenes

userGenes = UserGenes()
userGenes.authenticate()
userGenes.initTracksDF()

# print(userGenes.recentTracksDF.head())
print(userGenes.topTracksDF.head())
userGenes.topTracksDF.to_csv("topTracks.csv")

import pandas as pd


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


print(parse_spotify_data(userGenes.topTracksDF))
