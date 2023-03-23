import openai
import os
from dotenv import load_dotenv
from UserGenes import UserGenes


def load_env_variables():
    load_dotenv()
    openai.api_key = os.environ.get("OPENAI_API_KEY")


def init_user():
    user = UserGenes()
    user.initTracksDF()
    return user


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
