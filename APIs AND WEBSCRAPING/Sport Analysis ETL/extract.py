import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('API_KEY')
headers = {"X-Auth-Token": token}


def extract_competitions():
    response = requests.get('https://api.football-data.org/v4/competitions', headers=headers)
    response.raise_for_status()

    data = response.json()

    df_competitions = pd.DataFrame(data['competitions'])

    return df_competitions


def extract_teams(competition_id = 'PL'):
    response = requests.get(f'https://api.football-data.org/v4/competitions/{competition_id}/teams',
                            headers=headers)
    response.raise_for_status()
    data = response.json()

    df_teams = pd.DataFrame(data['teams'])
    return df_teams

def extract_matches(competition_id = 'PL'):
    response = requests.get(f'https://api.football-data.org/v4/competitions/{competition_id}/matches', 
                            headers=headers)
    response.raise_for_status()
    data = response.json()

    df_matches = pd.DataFrame(data['matches'])
    return df_matches



if __name__ == '__main__':
    competition_id = 'PL'

    df_competition = extract_competitions()
    df_teams = extract_teams()
    df_matches = extract_matches()

    params = [df_competition, df_matches, df_teams]
    for p in params:
        print(p.head())

