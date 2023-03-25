import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd
import pymongo
from datetime import datetime, timedelta

load_dotenv()


class UserGenes:
    def __init__(
        self,
        sp=spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope="user-library-read user-top-read user-read-recently-played",
                redirect_uri="http://localhost:5000/callback/",
            )
        ),
    ):
        self.sp = sp
        # self.mongoClient = pymongo.MongoClient(os.environ.get("MONGO_URI"))
        # self.mongoDB = self.mongoClient["SpotifyGenetics"]
        # self.recentTracksCollection = self.mongoDB["recentTracks"]
        self.authManager = SpotifyOAuth(
            scope="user-library-read user-top-read user-read-recently-played",
            redirect_uri="http://localhost:5000/callback/",
        )
        self.recentTracksDF = None
        self.topTracksDF = None
        self.topTrackIDs = []

        self.audioFeaturesDF = None
        self.readableGenes = None

    def isAuthenticated(self):
        token_info = self.authManager.get_cached_token()
        return self.authManager.validate_token(token_info)

    # Track information retrieval
    def initTracksDF(self):
        self.recentTracksDF = self.getRecentlyPlayed()
        self.recentTracksDF = self.addColumnsToDF(self.recentTracksDF)

    def addColumnsToDF(self, df):
        df["inLibrary"] = self.isInLibrary(df["id"])
        df = self.mergeAudioFeatures(df)
        return df

    def getTopTracks(self, limit=50):
        topTrackIDs = []
        for item in self.sp.current_user_top_tracks(limit=limit)["items"]:
            topTrackIDs.append(item["id"])

        return self.createTrackInfoDataFrame(topTrackIDs)

    def getRecentlyPlayed(self, limit=50):
        recentTracks = self.sp.current_user_recently_played(limit=limit)
        trackIds = [item["track"]["id"] for item in recentTracks["items"]]

        return self.createTrackInfoDataFrame(trackIds)

    def createTrackInfoDataFrame(self, trackIds) -> pd.DataFrame:
        trackInfo = self.sp.tracks(trackIds)["tracks"]
        artistIds = list(
            set([artist["id"] for track in trackInfo for artist in track["artists"]])
        )

        # Get the artist information using their IDs
        artistInfo = self.sp.artists(artistIds)["artists"]
        artistInfoDict = {
            artist["id"]: {
                "popularity": artist["popularity"],
                "genres": artist["genres"],
            }
            for artist in artistInfo
        }

        data = []

        for track in trackInfo:
            artist_names = [artist["name"] for artist in track["artists"]]
            artist_links = [
                artist["external_urls"]["spotify"] for artist in track["artists"]
            ]

            trackData = {
                "id": track["id"],
                "trackName": track["name"],
                "trackPopularity": f'{track["popularity"]} (0-100)',
                "trackDurationMs": f'{track["duration_ms"]} ms',
                "trackExplicit": track["explicit"],
                "albumName": track["album"]["name"],
                "albumType": track["album"]["album_type"],
                "albumReleaseDate": track["album"]["release_date"],
                "artistNames": artist_names,
                "artistLinks": artist_links,
                "artistID": track["artists"][0]["id"],
                "artistGenres": artistInfoDict[track["artists"][0]["id"]]["genres"],
                "artistPopularity": f'{artistInfoDict[track["artists"][0]["id"]]["popularity"]} (0-100)',
                "spotifyURL": track["external_urls"]["spotify"],
                "albumCoverURL": track["album"]["images"][0]["url"],
            }
            data.append(trackData)

        df = pd.DataFrame(data)
        return df

    def isInLibrary(self, track_ids):
        results = self.sp.current_user_saved_tracks_contains(tracks=track_ids)
        return results

    # Audio features
    def mergeAudioFeatures(self, df):
        audioFeatures = self.sp.audio_features(df["id"])
        self.audioFeaturesDF = pd.DataFrame(audioFeatures)
        df = pd.merge(df, self.audioFeaturesDF, on="id")

        self.addGeneColumn(df)
        return df

    # Gene calculation and analysis
    def calculateGene(self, row):
        # Calculate the mood score using valence and mode
        valence_weight = 0.8
        mode_weight = 0.2
        mood_score = valence_weight * row["valence"] + mode_weight * row["mode"]
        moodGene = "H" if mood_score > 0.5 else "S"

        paceGene = "F" if row["tempo"] > 100 else "L"

        # Calculate the complexity score using the selected features
        complexity_score = (
            -0.15 * row["instrumentalness"]
            + 0.25 * row["speechiness"]
            - 0.15 * row["acousticness"]
            + 0.2 * row["energy"]
            + 0.1 * row["danceability"]
            + 0.15
            * row["tempo"]
            / 200  # normalize tempo to [0, 1] by dividing by an approximate maximum value
            + 0.2
            * (
                1 if row["time_signature"] != 4 else 0
            )  # assign complexity based on time_signature
        )

        # Normalize the complexity score between 0 and 1
        complexity_score = (complexity_score + 1) / 2

        # Adjust the threshold to classify tracks as dense
        textureGene = "D" if complexity_score > 0.55 else "M"

        vocalsGene = "V" if row["instrumentalness"] < 0.5 else "I"

        return f"{moodGene}{paceGene}{textureGene}{vocalsGene}"

    def getOverallGenes(self):
        avgDF = {
            "energy": self.df["energy"].mean(),
            "mode": self.df["mode"].mean(),
            "tempo": self.df["tempo"].mean(),
            "acousticness": self.df["acousticness"].mean(),
        }

        return self.calculateGene(avgDF)

    def getGeneCounts(self):
        return (
            self.df["gene"]
            .value_counts()
            .apply(lambda x: x / self.df["gene"].count() * 100)
        )

    def displayGeneCounts(self):
        geneCounts = self.getGeneCounts()
        for gene, count in geneCounts.items():
            print(f"{gene}: {count:.2f}%")

    def getGeneExamples(self, trait):
        traitToColumn = {
            "energy": "energy",
            "mood": "valence",
            "tempo": "tempo",
            "instrumentation": "instrumentalness",
        }

        columnName = traitToColumn[trait]

        # Get top 3 examples
        topExamples = self.df.nlargest(3, columnName)[["name", "artists"]]
        topExamples["artists"] = topExamples["artists"].apply(lambda x: x[0])
        topExamples["Label"] = "Top"

        # Get 1 contrary example
        contraryExample = self.df.nsmallest(1, columnName)[["name", "artists"]]
        contraryExample["artists"] = contraryExample["artists"].apply(lambda x: x[0])
        contraryExample["Label"] = "Contrary"

        # Combine examples into a single dataframe and return
        examplesDf = pd.concat([topExamples, contraryExample])
        return examplesDf

    def getExamplesByGene(self, gene):
        return self.df[self.df["gene"] == gene]

    def getGeneDataFromDF(self, df):
        data = []
        for gene in df["gene"].unique():
            data.append(
                {
                    "genre": gene,
                    "count": int(df[df["gene"] == gene]["gene"].count()),
                }
            )
        return data

    def getRecommendationsByGene(self, df, seed_genre=None, limit=20):
        """
        Get music recommendations based on the user's genes and other seed criteria.
        :param seed_genre: a gene to use as seed criteria
        :param limit: the maximum number of recommendations to return
        :return: a list of recommended tracks, each represented as a dictionary with metadata
        """
        if seed_genre is None:
            raise ValueError("A seed genre must be provided.")

        self.readableGenes = df[df["gene"] == seed_genre]

        if self.readableGenes.empty:
            return []

        seed_artists = (
            self.readableGenes["artistID"]
            .sample(n=min(2, len(self.readableGenes)))
            .tolist()
        )
        seed_genre = (
            pd.Series(
                [
                    genre
                    for artistGenre in [
                        self.sp.artist(artist_id)["genres"]
                        for artist_id in seed_artists
                    ]
                    for genre in artistGenre
                ]
            )
            .sample(n=min(1, len(seed_genre)))
            .tolist()
        )
        seed_tracks = (
            self.readableGenes["id"].sample(n=min(2, len(self.readableGenes))).tolist()
        )

        recommendations = self.sp.recommendations(
            seed_artists=seed_artists,
            seed_tracks=seed_tracks,
            limit=limit,
        )

        recommendationsDF = self.createTrackInfoDataFrame(
            list(pd.DataFrame(recommendations["tracks"])["id"])
        )

        recommendationsDF = self.addColumnsToDF(recommendationsDF)

        return recommendationsDF

    def addGeneColumn(self, df):
        df["gene"] = df.apply(self.calculateGene, axis=1)

    def getRecentlyPlayedForCard(self, limit=50):
        recentTracks = (
            self.recentTracksDF[
                [
                    "trackName",
                    "artistNames",
                    "albumCoverURL",
                    "spotifyURL",
                    "gene",
                    "inLibrary",
                ]
            ]
            .drop_duplicates(subset=("trackName", "spotifyURL"))
            .copy()
        )
        recentTracksList = recentTracks.to_dict("records")

        return [
            {
                "name": track["trackName"],
                "artist": ", ".join(track["artistNames"]),
                "image_url": track["albumCoverURL"],
                "url": track["spotifyURL"],
                "gene": track["gene"],
                "is_in_library": track["inLibrary"],
            }
            for track in recentTracksList
        ]

    def getTopTracksForCard(self, limit=50):
        topTracks = self.topTracksDF[
            ["trackName", "artistNames", "albumCoverURL", "spotifyURL", "inLibrary"]
        ]

        topTracksList = topTracks.to_dict("records")

        return [
            {
                "name": track["trackName"],
                "artist": ", ".join(track["artistNames"]),
                "image_url": track["albumCoverURL"],
                "url": track["spotifyURL"],
                "is_in_library": track["inLibrary"],
            }
            for track in topTracksList
        ]

    # Helper functions
    def getGeneBySongID(self, song_id):
        audioFeatures = self.sp.audio_features([song_id])[0]
        avgDF = {
            "energy": audioFeatures["energy"],
            "mode": audioFeatures["mode"],
            "tempo": audioFeatures["tempo"],
            "acousticness": audioFeatures["acousticness"],
        }
        gene = self.calculateGene(avgDF)
        return gene
