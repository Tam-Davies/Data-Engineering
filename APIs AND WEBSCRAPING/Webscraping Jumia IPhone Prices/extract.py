import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

headers = {
    "User-Agent": "DataEngineeringPracticeBot/1.0 (your.email@example.com; personal learning project)"}
base_url = 'https://www.jumia.com.ng/mlp-stay-connected-deals/ios-phones'


def extract_data(page):
    response = requests.get(f'{base_url}/?page={page}#catalog-listing', 
                            headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    view = soup.find('div', class_='-phm -pvxs row _no-g _4cl-3cm-shs')
    column_titles = ['Name', 'new_price', 'old_price', 'discount']
    articles = view.find_all('article', class_='prd _fb col c-prd')
    all_iphone_products = []
    for article in articles:
        infos = article.find('div', class_='info')
        # print(info.text.strip())
        name = infos.find('h3', class_='name').text.strip()
        new_price = infos.find('div', class_='prc').text.strip()
        old_price_tag = infos.find('div', class_='old')
        old_price = old_price_tag.text.strip() if old_price_tag else None
        discount_tag = infos.find('div', class_='bdg _dsct _sm')
        discount = discount_tag.text.strip() if discount_tag else None
        data = [name, new_price, old_price, discount]
        all_iphone_products.append(data)

    phone_details = pd.DataFrame(all_iphone_products, columns=column_titles)
    return phone_details

    


import time

if __name__ == '__main__':
    all_pages = []
    for page in range(1, 16):
        print(f"Scraping page {page}...")
        df_page = extract_data(page)
        all_pages.append(df_page)
        time.sleep(0.5)  

    df = pd.concat(all_pages, ignore_index=True)
    df.to_csv('Webscraping Jumia Iphone Prices/jumia_iphone_prices.csv', index=False)
    print(df.head())
    print(df.shape)