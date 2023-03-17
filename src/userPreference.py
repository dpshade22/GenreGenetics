import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


class UserPreferences:
    def __init__(self):
        self.authManager = SpotifyOAuth(
            scope="user-library-read user-top-read user-read-recently-played",
            redirect_uri="http://localhost:8000/callback/",
        )
        self.sp = spotipy.Spotify(auth_manager=self.authManager)
        self.energyCategories = {}
        self.moodCategories = {}
        self.tempoCategories = {}
        self.instrumentationCategories = {}
        self.topTracks = None
        self.df = None
        self.audioFeaturesDF = None
        self.readablePreferences = None

    def authenticate(self):
        # Access token is valid, initialize Spotify client
        self.sp = spotipy.Spotify(auth_manager=self.authManager)

    def initTopTracksDF(self):
        self.getTopTracks()
        self.getAudioFeatures()

    def getTopTracks(self, limit=100):
        self.topTracks = self.sp.current_user_top_tracks(limit=limit)
        self._createDataframe()

    def getAudioFeatures(self):
        audioFeatures = self.sp.audio_features(self.df["id"])
        self.audioFeaturesDF = pd.DataFrame(audioFeatures)
        self.df = pd.merge(self.df, self.audioFeaturesDF, on="id")
        self._addPreferenceColumn()

    def getOverallPreferences(self):
        avgDF = {
            "energy": self.df["energy"].mean(),
            "mode": self.df["mode"].mean(),
            "tempo": self.df["tempo"].mean(),
            "acousticness": self.df["acousticness"].mean(),
        }

        return self._calculatePreference(avgDF)

    def getPreferenceCounts(self):
        return (
            self.df["preference"]
            .value_counts()
            .apply(lambda x: x / self.df["preference"].count() * 100)
        )

    def displayPreferenceCounts(self):
        preferenceCounts = self.getPreferenceCounts()
        for preference, count in preferenceCounts.items():
            print(f"{preference}: {count:.2f}%")

    def getPreferenceExamples(self, trait):
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

    def getExamplesByPreference(self, preference):
        return self.df[self.df["preference"] == preference]

    def getPreferenceData(self):
        data = []
        for genre in self.df["preference"].unique():
            data.append(
                {
                    "genre": genre,
                    "count": int(
                        self.df[self.df["preference"] == genre]["preference"].count()
                    ),
                }
            )
        return data

    def _createDataframe(self):
        self.df = pd.DataFrame(self.topTracks["items"])
        self.df.drop_duplicates(subset="id", inplace=True)

    def _calculatePreference(self, row):
        energyPreference = "H" if row["energy"] > 0.5 else "L"
        moodPreference = "P" if row["mode"] > 0.49 else "N"
        tempoPreference = "F" if row["tempo"] > 100 else "S"
        instrumentationPreference = "E" if row["acousticness"] < 0.5 else "A"
        return f"{energyPreference}{moodPreference}{tempoPreference}{instrumentationPreference}"

    def _addPreferenceColumn(self):
        self.df["preference"] = self.df.apply(self._calculatePreference, axis=1)

    def getPrettyGenreDF(self, genre):
        tempDF = self.df[["name", "artists", "preference"]]
        tempDF["artists"] = self.df.apply(lambda x: x["artists"][0]["name"], axis=1)
        tempDF["artistLink"] = self.df.apply(
            lambda x: x["artists"][0]["external_urls"]["spotify"], axis=1
        )
        tempDF["songLink"] = self.df.apply(
            lambda x: x["external_urls"]["spotify"], axis=1
        )
        self.readablePreferences = tempDF
        return tempDF[tempDF["preference"] == genre]

    def getRecentlyPlayed(self, limit=10):
        recentlyPlayed = self.sp.current_user_recently_played(limit=limit)
        recentlyPlayedPretty = [
            {
                "name": item["track"]["name"],
                "artist": item["track"]["artists"][0]["name"],
                "url": item["track"]["external_urls"]["spotify"],
            }
            for item in recentlyPlayed["items"]
        ]
        return recentlyPlayedPretty
