import os
import requests
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")

BASE_URL = "https://api.themoviedb.org/3"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "accept": "application/json"
}


def extract_popular_movies():

    url = f"{BASE_URL}/movie/popular"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return pd.DataFrame(data["results"])


def extract_popular_tv():

    url = f"{BASE_URL}/tv/popular"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return pd.DataFrame(data["results"])


def extract_movie_list():

    url = f"{BASE_URL}/genre/movie/list"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return pd.DataFrame(data["genres"])


if __name__ == "__main__":

    df_movies = extract_popular_movies()
    df_tv = extract_popular_tv()
    df_genres = extract_movie_list()

    # print("Movies:")
    # print(df_movies.info())

    # print("\nTV:")
    # print(df_tv.info())

    print("\nGenres:")
    print(df_genres.info())