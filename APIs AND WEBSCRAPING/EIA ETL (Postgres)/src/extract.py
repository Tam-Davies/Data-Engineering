import pandas as pd
import requests
from dotenv import load_dotenv
import os

base_url = 'https://api.eia.gov/v2/petroleum/crd/crpdn/data/'

load_dotenv()
api_key = os.getenv("EIA_API_KEY")

series_codes = [
    "MANFPAK1", "MANFPAK2", "MCRFP3FM1", "MCRFP3FM2", "MCRFP5F1", "MCRFP5F2",
    "MCRFPAK1", "MCRFPAK2", "MCRFPAKS1", "MCRFPAKS2", "MCRFPAL1", "MCRFPAL2",
    "MCRFPAR1", "MCRFPAR2", "MCRFPAZ1", "MCRFPAZ2", "MCRFPCA1", "MCRFPCA2",
    "MCRFPCO1", "MCRFPCO2", "MCRFPFL1", "MCRFPFL2", "MCRFPIL1", "MCRFPIL2",
    "MCRFPIN1", "MCRFPIN2", "MCRFPKS1", "MCRFPKS2", "MCRFPKY1", "MCRFPKY2",
    "MCRFPLA1", "MCRFPLA2", "MCRFPMO1", "MCRFPMO2", "MCRFPMS1", "MCRFPMS2",
    "MCRFPMT1", "MCRFPMT2", "MCRFPND1", "MCRFPND2", "MCRFPNE1", "MCRFPNE2",
    "MCRFPNM1", "MCRFPNM2", "MCRFPNV1", "MCRFPNV2", "MCRFPNY1", "MCRFPNY2",
    "MCRFPOH1", "MCRFPOH2", "MCRFPOK1", "MCRFPOK2", "MCRFPP11", "MCRFPP12",
    "MCRFPP21", "MCRFPP22", "MCRFPP31", "MCRFPP32", "MCRFPP41", "MCRFPP42",
    "MCRFPP51", "MCRFPP52", "MCRFPPA1", "MCRFPPA2", "MCRFPSD1", "MCRFPSD2",
    "MCRFPTN1", "MCRFPTN2", "MCRFPTX1", "MCRFPTX2", "MCRFPUS1", "MCRFPUS2",
    "MCRFPUT1", "MCRFPUT2", "MCRFPVA1", "MCRFPVA2", "MCRFPWV1", "MCRFPWV2",
    "MCRFPWY1", "MCRFPWY2", "MCRFP_SMI_1", "MCRFP_SMI_2",
    "M_EPC0_FPF_SID_MBBL", "M_EPC0_FPF_SID_MBBLD",
]

params = {
    "api_key": api_key,
    "frequency": "annual",
    "data[0]": "value",
    "start": "2010",
    "end": "2026",
    "sort[0][column]": "period",
    "sort[0][direction]": "desc",
    "offset": 0,
    "length": 5000,
}
params_list = list(params.items()) + [("facets[series][]", s) for s in series_codes]

response = requests.get(base_url, params=params_list)

def extract_data():
    url = base_url
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(data['response']['data'])
    return df


# if __name__ == '__main__':
#     df = extract_data()
#     print(df['process'])