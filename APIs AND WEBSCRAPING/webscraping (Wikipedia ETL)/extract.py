from bs4 import BeautifulSoup
import requests
import pandas as pd


URL = "https://en.wikipedia.org/wiki/List_of_largest_companies_in_the_United_States_by_revenue"

HEADERS = {
    "User-Agent": "DataEngineeringPracticeBot/1.0 (your.email@example.com; personal learning project)"
}


def extract_data():
    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")

    headers = table.find_all("th")
    columns = [header.get_text(strip=True) for header in headers]

    rows = table.find_all("tr")[1:]

    data = []

    # for row in rows:
    #     cells = row.find_all("td")
    #     row_data = [cell.get_text(strip=True) for cell in cells]
    #     data.append(row_data)
    for row in rows:
        cells = row.find_all("td")

        if not cells:
           continue

        row_data = [cell.get_text(strip=True) for cell in cells]

        if len(row_data) == len(columns):
           data.append(row_data)

    df = pd.DataFrame(data, columns=columns)

    return df


if __name__ == "__main__":

    df = extract_data()

    df.to_csv("webscraping (Wikipedia ETL)/US_REVENUE_DATA.csv", index=False)

    print(df.head())
    print(df.shape)