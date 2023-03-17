import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


class UserGenes:
    def __init__(self):
        self.authManager = SpotifyOAuth(
            scope="user-library-read user-top-read user-read-recently-played",
            redirect_uri="http://localhost:8000/callback/",
        )
        self.sp = spotipy.Spotify(auth_manager=self.authManager)
        self.topTracks = None
        self.df = None
        self.recentTracks = None
        self.audioFeaturesDF = None
        self.readableGenes = None

    # Authentication
    def authenticate(self):
        self.sp = spotipy.Spotify(auth_manager=self.authManager)

    # Track information retrieval
    def initTracksDF(self):
        self.getRecentlyPlayed()
        self._createDataframe()
        self.getAudioFeatures()

    def getTopTracks(self, limit=100):
        self.topTracks = self.sp.current_user_top_tracks(limit=limit)

    def getRecentlyPlayed(self, limit=50):
        self.recentTracks = self.sp.current_user_recently_played(limit=limit)

    # Audio features
    def getAudioFeatures(self):
        audioFeatures = self.sp.audio_features(self.df["id"])
        self.audioFeaturesDF = pd.DataFrame(audioFeatures)
        self.df = pd.merge(self.df, self.audioFeaturesDF, on="id")
        self._addGeneColumn()

    # Gene calculation and analysis
    def _calculateGene(self, row):
        energyGene = "H" if row["energy"] > 0.5 else "L"
        moodGene = "P" if row["mode"] > 0.49 else "N"
        tempoGene = "F" if row["tempo"] > 100 else "S"
        instrumentationGene = "E" if row["acousticness"] < 0.5 else "A"
        return f"{energyGene}{moodGene}{tempoGene}{instrumentationGene}"

    def getOverallGenes(self):
        avgDF = {
            "energy": self.df["energy"].mean(),
            "mode": self.df["mode"].mean(),
            "tempo": self.df["tempo"].mean(),
            "acousticness": self.df["acousticness"].mean(),
        }

        return self._calculateGene(avgDF)

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

    def getGeneData(self):
        data = []
        for genre in self.df["gene"].unique():
            data.append(
                {
                    "genre": genre,
                    "count": int(self.df[self.df["gene"] == genre]["gene"].count()),
                }
            )
        return data

    def getRecommendationsByGene(self, seed_genre=None, limit=20):
        """
        Get music recommendations based on the user's genes and other seed criteria.
        :param seed_genre: a gene to use as seed criteria
        :param limit: the maximum number of recommendations to return
        :return: a list of recommended tracks, each represented as a dictionary with metadata
        """
        if seed_genre is None:
            raise ValueError("A seed genre must be provided.")

        self.getPrettyGenreDF(seed_genre)

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
            # seed_genre=seed_genre,
            seed_tracks=seed_tracks,
            limit=limit,
        )

        return recommendations["tracks"]

    def _createDataframe(self):
        if self.topTracks:
            track_data = [
                {
                    "id": item["id"],
                    "trackName": item["name"],
                    "artists": [
                        {
                            "name": artist["name"],
                            "spotify_url": artist["external_urls"]["spotify"],
                            "artistID": artist["id"],
                        }
                        for artist in item["artists"]
                    ],
                    "spotify_url": item["external_urls"]["spotify"],
                }
                for item in self.topTracks["items"]
            ]
            self.df = pd.DataFrame(track_data)
        elif self.recentTracks:
            track_data = [
                {
                    "id": item["track"]["id"],
                    "trackName": item["track"]["name"],
                    "artistName": [
                        {
                            "name": artist["name"],
                            "spotify_url": artist["external_urls"]["spotify"],
                            "artistID": artist["id"],
                        }
                        for artist in item["track"]["artists"]
                    ],
                    "spotify_url": item["track"]["external_urls"]["spotify"],
                }
                for item in self.recentTracks["items"]
            ]
            self.df = pd.DataFrame(track_data)
        else:
            raise ValueError(
                "At least one of 'topTracks' or 'recentTracks' must be True."
            )
        # Drop duplicates based on track ID
        self.df.drop_duplicates(subset="id", inplace=True)

    def _addGeneColumn(self):
        self.df["gene"] = self.df.apply(self._calculateGene, axis=1)

    def getPrettyGenreDF(self, genre):
        tempDF = self.df[self.df["gene"] == genre]
        tempDF = tempDF[["id", "trackName", "artistName", "spotify_url"]].copy()

        tempDF["artists"] = tempDF["artistName"].apply(
            lambda x: ", ".join([artist["name"] for artist in x])
        )
        tempDF["artistLink"] = tempDF["artistName"].apply(
            lambda x: x[0]["spotify_url"] if x else None
        )
        tempDF["trackLink"] = tempDF["spotify_url"]
        tempDF["artistID"] = tempDF["artistName"].apply(
            lambda x: x[0]["artistID"] if x else None
        )
        self.readableGenes = tempDF

        return tempDF[["trackName", "artists", "trackLink", "artistLink"]]

    def getRecentlyPlayed(self, limit=50):
        self.recentTracks = self.sp.current_user_recently_played(limit=limit)
        recentlyPlayedPretty = [
            {
                "name": item["track"]["name"],
                "artist": item["track"]["artists"][0]["name"],
                "url": item["track"]["external_urls"]["spotify"],
                "gene": self._getGeneBySongID(item["track"]["id"]),
                "image_url": item["track"]["album"]["images"][0]["url"],
            }
            for item in self.recentTracks["items"]
        ]
        return recentlyPlayedPretty

    # Helper functions
    def _getGeneBySongID(self, song_id):
        audioFeatures = self.sp.audio_features([song_id])[0]
        avgDF = {
            "energy": audioFeatures["energy"],
            "mode": audioFeatures["mode"],
            "tempo": audioFeatures["tempo"],
            "acousticness": audioFeatures["acousticness"],
        }
        gene = self._calculateGene(avgDF)
        return gene
