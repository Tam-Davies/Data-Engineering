import os
import requests
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

def get_access_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret)
    )
    response.raise_for_status()
    return response.json()["access_token"]




def extract_albums(access_token):
    headers = {
    "Authorization": f"Bearer {access_token}",
    "accept": "application/json"}
    url = 'https://api.spotify.com/v1/albums/382ObEPsp2rxGrnsizN5TX'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    df_albums = pd.DataFrame([data])
    return df_albums

# def extract_artists(access_token):
#     headers = {
#     "Authorization": f"Bearer {access_token}",
#     "accept": "application/json"}
#     url = 'https://api.spotify.com/v1/artists?ids=2CIMQHirSU0MQqyYHq0eOx%2C57dN52uHvrHOxijzpIgu3E%2C1vCWHaC5f2uS3yhpwWbIA6'
#     response = requests.get(url, headers=headers)
#     response.raise_for_status()

#     data = response.json()
#     df_artists = pd.DataFrame(data['artists'])
#     return df_artists


# def extract_tracks(access_token):
#     headers = {
#     "Authorization": f"Bearer {access_token}",
#     "accept": "application/json"}
#     url = 'https://api.spotify.com/v1/tracks?ids=7ouMYWpwJ422jRcDASZB7P%2C4VqPOruhp5EdPBeR92t6lQ%2C2takcwOaAZWiXQijPHIx7B'
#     response = requests.get(url, headers=headers)
#     response.raise_for_status()

#     data = response.json()
#     df_tracks = pd.DataFrame(data['tracks'])
#     return df_tracks




if __name__ == "__main__":
    access_token = get_access_token()

    df_albums = extract_albums(access_token)
    # df_artists = extract_artists(access_token)
    # df_tracks = extract_tracks(access_token)

    print(df_albums.keys())
    # print(df_artists.head())
    # print(df_tracks.head())