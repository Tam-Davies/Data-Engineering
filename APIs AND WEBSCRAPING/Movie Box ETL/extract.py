import os
import requests
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
token = os.getenv("TMDB_READ_ACCESS_TOKEN")

headers = {
    "Authorization": f"Bearer {token}",
    "accept": "application/json"
}

def extract_popular_movies():
    response = requests.get('https://api.themoviedb.org/3/movie/popular', headers=headers)
    response.raise_for_status()

    data = response.json()
    df_popular_movies = pd.DataFrame(data['results'])

    return df_popular_movies


def extract_popular_tv():
    response = requests.get('https://api.themoviedb.org/3/tv/popular', headers=headers)
    response.raise_for_status()

    data = response.json()
    df_popular_tv = pd.DataFrame(data['results'])

    return df_popular_tv


def extract_movie_list():
    response = requests.get('https://api.themoviedb.org/3/genre/movie/list', headers=headers)
    response.raise_for_status()

    data = response.json()
    df_movie_list = pd.DataFrame(data['genres'])

    return df_movie_list


df_movies = extract_popular_movies()
df_tv = extract_popular_tv()
df_genres = extract_movie_list()

print(df_movies.head())
print(df_tv.head())
print(df_genres.head())