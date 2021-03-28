import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
from google_trans_new import google_translator
from typing import Dict
from logging import Logger
import pickle
import os


def get_info(origin: str, destination: str,
             page=None, country_id: int = None,
             origin_id: int = None, destination_id: int = None,
             total_size: int = None, hash_id: str = None,
             order: int = None, date: str = None, logger: Logger = None) -> Dict:
    translator = google_translator()
    translated_origin = translator.translate(origin, lang_src='en', lang_tgt='ru')
    translated_dest = translator.translate(destination, lang_src='en', lang_tgt='ru')

    if not os.path.isdir('./pickles/avtobeket.pickle'):
        res = requests.get("https://avtobeket.kg/routes/")
        soup = BeautifulSoup(res.content, 'lxml')
        bus_routes_table = soup.find_all('table')[1]
        df2 = pd.read_html(str(bus_routes_table))[0]
        pd.set_option("display.max_rows", None, "display.max_columns", None)
        df2.to_latex(index=False)
        df2 = df2.dropna(subset=[1])
        df2.to_pickle('avtobeket.pickle', compression='infer', protocol=5)
        data = df2.loc[
            (df2[1] ==
             translated_origin + " – " + translated_dest) |
            (df2[1] == translated_origin + "-" + translated_dest) |
            (df2[1] == translated_origin + " — " + translated_dest)
            ]
    else:
        df = pd.read_pickle('pickles/avtobeket.pickle')
        data = df.loc[
            (df[1] ==
             translated_origin + " – " + translated_dest) |
            (df[1] == translated_origin + "-" + translated_dest) |
            (df[1] == translated_origin + " — " + translated_dest)
            ]
    return data
